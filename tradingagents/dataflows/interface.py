from typing import Annotated, Dict
from .reddit_utils import fetch_top_from_category
from .googlenews_utils import getNewsData # Import specific function
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import json
import os
import pandas as pd
from tqdm import tqdm
from openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import httpx # Add httpx import for OpenAI client
from .config import get_config, set_config, DATA_DIR
from .crypto_utils import get_crypto_ohlcv_data_window, get_crypto_current_price, get_crypto_order_book, get_blockchain_data, get_crypto_technical_indicators_data # Import specific functions


def get_google_news(
    query: Annotated[str, "Query to search with (e.g., 'Bitcoin', 'Ethereum news')"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    # Add cryptocurrency specific keywords to the query if it's a crypto symbol
    if "/" in query or query.upper() in ["BTC", "ETH", "XRP", "LTC", "BCH"]:
        query = f"{query} cryptocurrency OR blockchain OR crypto news"
    
    query = query.replace(" ", "+")

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    news_results = getNewsData(query, before, curr_date)

    news_str = ""

    for news in news_results:
        news_str += (
            f"### {news['title']} (source: {news['source']}) \n\n{news['snippet']}\n\n"
        )

    if len(news_results) == 0:
        return ""

    return f"## {query} Google News, from {before} to {curr_date}:\n\n{news_str}"


def get_reddit_global_news(
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    posts = []
    # iterate from start_date to end_date
    curr_date = datetime.strptime(before, "%Y-%m-%d")

    total_iterations = (start_date - curr_date).days + 1
    pbar = tqdm(desc=f"Getting Global News on {start_date}", total=total_iterations)

    while curr_date <= start_date:
        curr_date_str = curr_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "global_news",
            curr_date_str,
            max_limit_per_day,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date += relativedelta(days=1)
        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"## Global News Reddit, from {before} to {curr_date}:\n{news_str}"


def get_reddit_company_news(
    symbol: Annotated[str, "The cryptocurrency symbol (e.g., 'BTC', 'ETH') or company ticker symbol (e.g., 'AAPL')"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news for a given cryptocurrency or company.
    Args:
        symbol: The cryptocurrency symbol or company ticker symbol.
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    before_dt = start_date_dt - relativedelta(days=look_back_days)
    before_str = before_dt.strftime("%Y-%m-%d")

    posts = []
    curr_date_iter = datetime.strptime(before_str, "%Y-%m-%d")

    total_iterations = (start_date_dt - curr_date_iter).days + 1
    pbar = tqdm(
        desc=f"Getting Company/Crypto News for {symbol} on {start_date}",
        total=total_iterations,
    )

    while curr_date_iter <= start_date_dt:
        curr_date_str = curr_date_iter.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "company_news", # This category name might need to be generalized or a new one created for crypto
            curr_date_str,
            max_limit_per_day,
            symbol, # Pass the symbol directly as the query
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date_iter += relativedelta(days=1)

        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"##{symbol} News Reddit, from {before_str} to {start_date}:\n\n{news_str}"




from langchain.tools import Tool
from typing import Annotated, Dict, Any
from .reddit_utils import fetch_top_from_category
from .googlenews_utils import getNewsData
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import json
import os
import pandas as pd
from tqdm import tqdm
from openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import httpx
from .config import get_config, set_config, DATA_DIR
from .crypto_utils import get_crypto_ohlcv_data_window, get_crypto_current_price, get_crypto_order_book, get_blockchain_data, get_crypto_technical_indicators_data

class Toolkit:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.summarize_text = Tool(
            name="summarize_text",
            func=self._summarize_text,
            description="Summarize a given text to a specified character limit.",
        )
        self.get_google_news = Tool(
            name="get_google_news",
            func=get_google_news,
            description="Retrieve news articles from Google News based on a query and date range. Args: query (str), curr_date (str), look_back_days (int)",
        )
        self.get_reddit_global_news = Tool(
            name="get_reddit_global_news",
            func=get_reddit_global_news,
            description="Retrieve top global news posts from Reddit for a given date range. Args: start_date (str), look_back_days (int), max_limit_per_day (int)",
        )
        self.get_reddit_company_news = Tool(
            name="get_reddit_company_news",
            func=get_reddit_company_news,
            description="Retrieve top Reddit news posts for a specific cryptocurrency or company. Args: symbol (str), start_date (str), look_back_days (int), max_limit_per_day (int)",
        )
        self.get_crypto_ohlcv_data_window = Tool(
            name="get_crypto_ohlcv_data_window",
            func=get_crypto_ohlcv_data_window,
            description="Retrieve OHLCV data for a cryptocurrency pair within a time frame. Args: exchange_id (str), symbol (str), timeframe (str), curr_date (str), look_back_days (int)",
        )
        self.get_crypto_current_price = Tool(
            name="get_crypto_current_price",
            func=get_crypto_current_price,
            description="Retrieve the current price of a cryptocurrency pair. Args: exchange_id (str), symbol (str)",
        )
        self.get_crypto_order_book = Tool(
            name="get_crypto_order_book",
            func=get_crypto_order_book,
            description="Retrieve the order book for a cryptocurrency pair. Args: exchange_id (str), symbol (str), limit (int)",
        )
        self.get_blockchain_data = Tool(
            name="get_blockchain_data",
            func=get_blockchain_data,
            description="Fetches various types of blockchain data. This is a placeholder and needs to be implemented with actual API calls. Args: blockchain_id (str), data_type (str), address (str, optional), curr_date (str, optional), look_back_days (int, optional)",
        )
        self.get_crypto_technical_indicators = Tool(
            name="get_crypto_technical_indicators",
            func=get_crypto_technical_indicators_data,
            description="Retrieve technical indicators for a given cryptocurrency. Args: symbol (str), curr_date (str), look_back_days (int), exchange_id (str, optional), timeframe (str, optional)",
        )

    def _summarize_text(self, text: str, char_limit: int = 1500) -> str:
        """Summarize a given text to a specified character limit."""
        if not text:
            return ""
        if len(text) <= char_limit:
            return text
        return text[:char_limit] + "..."

# The individual functions are still defined outside the class as they are imported by the Toolkit.
# No changes needed for the functions themselves.

def get_google_news(
    query: Annotated[str, "Query to search with (e.g., 'Bitcoin', 'Ethereum news')"],
    curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    # Add cryptocurrency specific keywords to the query if it's a crypto symbol
    if "/" in query or query.upper() in ["BTC", "ETH", "XRP", "LTC", "BCH"]:
        query = f"{query} cryptocurrency OR blockchain OR crypto news"
    
    query = query.replace(" ", "+")

    start_date = datetime.strptime(curr_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    news_results = getNewsData(query, before, curr_date)

    news_str = ""

    for news in news_results:
        news_str += (
            f"### {news['title']} (source: {news['source']}) \n\n{news['snippet']}\n\n"
        )

    if len(news_results) == 0:
        return ""

    return f"## {query} Google News, from {before} to {curr_date}:\n\n{news_str}"


def get_reddit_global_news(
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news
    Args:
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    before = start_date - relativedelta(days=look_back_days)
    before = before.strftime("%Y-%m-%d")

    posts = []
    # iterate from start_date to end_date
    curr_date = datetime.strptime(before, "%Y-%m-%d")

    total_iterations = (start_date - curr_date).days + 1
    pbar = tqdm(desc=f"Getting Global News on {start_date}", total=total_iterations)

    while curr_date <= start_date:
        curr_date_str = curr_date.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "global_news",
            curr_date_str,
            max_limit_per_day,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date += relativedelta(days=1)
        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"## Global News Reddit, from {before} to {curr_date}:\n{news_str}"


def get_reddit_company_news(
    symbol: Annotated[str, "The cryptocurrency symbol (e.g., 'BTC', 'ETH') or company ticker symbol (e.g., 'AAPL')"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
    max_limit_per_day: Annotated[int, "Maximum number of news per day"],
) -> str:
    """
    Retrieve the latest top reddit news for a given cryptocurrency or company.
    Args:
        symbol: The cryptocurrency symbol or company ticker symbol.
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format
    Returns:
        str: A formatted dataframe containing the latest news articles posts on reddit and meta information in these columns: "created_utc", "id", "title", "selftext", "score", "num_comments", "url"
    """

    start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")
    before_dt = start_date_dt - relativedelta(days=look_back_days)
    before_str = before_dt.strftime("%Y-%m-%d")

    posts = []
    curr_date_iter = datetime.strptime(before_str, "%Y-%m-%d")

    total_iterations = (start_date_dt - curr_date_iter).days + 1
    pbar = tqdm(
        desc=f"Getting Company/Crypto News for {symbol} on {start_date}",
        total=total_iterations,
    )

    while curr_date_iter <= start_date_dt:
        curr_date_str = curr_date_iter.strftime("%Y-%m-%d")
        fetch_result = fetch_top_from_category(
            "company_news",
            curr_date_str,
            max_limit_per_day,
            symbol,
            data_path=os.path.join(DATA_DIR, "reddit_data"),
        )
        posts.extend(fetch_result)
        curr_date_iter += relativedelta(days=1)

        pbar.update(1)

    pbar.close()

    if len(posts) == 0:
        return ""

    news_str = ""
    for post in posts:
        if post["content"] == "":
            news_str += f"### {post['title']}\n\n"
        else:
            news_str += f"### {post['title']}\n\n{post['content']}\n\n"

    return f"##{symbol} News Reddit, from {before_str} to {start_date}:\n\n{news_str}"


def get_crypto_technical_indicators(
    symbol: Annotated[str, "The cryptocurrency symbol (e.g., 'BTC', 'ETH')"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """
    Retrieve technical indicators for a given cryptocurrency.
    Args:
        symbol: The cryptocurrency symbol.
        curr_date: Current date in yyyy-mm-dd format.
        look_back_days: How many days to look back for data.
    Returns:
        str: A formatted string containing the technical indicators.
    """
    indicators_df = get_crypto_technical_indicators_data(symbol, curr_date, look_back_days)
    if indicators_df.empty:
        return f"No technical indicators data found for {symbol} from {look_back_days} days before {curr_date} to {curr_date}."

    # Format the DataFrame into a readable string
    indicators_str = f"## Technical Indicators for {symbol} from {look_back_days} days before {curr_date} to {curr_date}:\n\n"
    indicators_str += indicators_df.to_string()
    return indicators_str
