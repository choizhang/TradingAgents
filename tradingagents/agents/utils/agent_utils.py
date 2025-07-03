from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from typing import List
from typing import Annotated
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import RemoveMessage
from langchain_core.tools import tool
from datetime import date, timedelta, datetime
import functools
import pandas as pd
import os
from dateutil.relativedelta import relativedelta
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
import tradingagents.dataflows.interface as interface
from tradingagents.default_config import DEFAULT_CONFIG
from langchain_core.messages import HumanMessage
import httpx # Add httpx import for OpenAI client


def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]
        
        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        
        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")
        
        return {"messages": removal_operations + [placeholder]}
    
    return delete_messages


class Toolkit:
    _config = DEFAULT_CONFIG.copy()

    @classmethod
    def update_config(cls, config):
        """Update the class-level configuration."""
        cls._config.update(config)

    @property
    def config(self):
        """Access the configuration."""
        return self._config

    def __init__(self, config=None):
        if config:
            self.update_config(config)

    @staticmethod
    @tool
    def get_reddit_news(
        curr_date: Annotated[str, "Date you want to get news for in yyyy-mm-dd format"],
    ) -> str:
        """
        Retrieve global news from Reddit within a specified time frame.
        Args:
            curr_date (str): Date you want to get news for in yyyy-mm-dd format
        Returns:
            str: A formatted dataframe containing the latest global news from Reddit in the specified time frame.
        """
        
        global_news_result = interface.get_reddit_global_news(curr_date, 3, 2)

        return global_news_result

    @staticmethod
    @tool
    def get_reddit_company_news(
        symbol: Annotated[str, "The cryptocurrency symbol (e.g., 'BTC', 'ETH') or company ticker symbol (e.g., 'AAPL')"],
        curr_date: Annotated[str, "Current date you want to get news for"],
    ) -> str:
        """
        Retrieve the latest news about a given cryptocurrency or company from Reddit, given the current date.
        Args:
            symbol (str): The cryptocurrency symbol or company ticker symbol.
            curr_date (str): current date in yyyy-mm-dd format to get news for
        Returns:
            str: A formatted string containing the latest news about the cryptocurrency/company on the given date.
        """
        # The interface.get_reddit_company_news function already handles the logic for crypto/company
        news_results = interface.get_reddit_company_news(symbol, curr_date, 3, 2)
        return news_results


    @staticmethod
    @tool
    def get_crypto_ohlcv_data_window(
        exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'kraken')"] = "kraken",
        symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"] = "BTC/USDT",
        timeframe: Annotated[str, "The OHLCV timeframe (e.g., '1m', '5m', '1h', '1d')"] = "1d",
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"] = datetime.now().strftime("%Y-%m-%d"),
        look_back_days: Annotated[int, "how many days to look back"] = 30,
    ) -> str:
        """
        Retrieve OHLCV data for a cryptocurrency pair within a time frame from local cache or online.
        """
        return interface.get_crypto_ohlcv_data_window(exchange_id, symbol, timeframe, curr_date, look_back_days)

    @staticmethod
    @tool
    def get_crypto_technical_indicators(
        symbol: Annotated[str, "The cryptocurrency symbol (e.g., 'BTC', 'ETH')"],
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
        look_back_days: Annotated[int, "how many days to look back"],
    ) -> str:
        """
        Retrieve technical indicators for a given cryptocurrency.
        """
        return interface.get_crypto_technical_indicators(symbol, curr_date, look_back_days)


    @staticmethod
    @tool
    def get_crypto_current_price(
        exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
        symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
    ) -> str:
        """
        Retrieve the current price of a cryptocurrency pair.
        """
        return interface.get_crypto_current_price(exchange_id, symbol)

    @staticmethod
    @tool
    def get_crypto_order_book(
        exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
        symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
        limit: Annotated[int, "Number of bids and asks to fetch"],
    ) -> str:
        """
        Retrieve the order book for a cryptocurrency pair.
        """
        return interface.get_crypto_order_book(exchange_id, symbol, limit)

    @staticmethod
    @tool
    def get_blockchain_data(
        blockchain_id: Annotated[str, "The ID of the blockchain (e.g., 'btc', 'eth')"],
        data_type: Annotated[str, "Type of blockchain data (e.g., 'address_balance', 'transaction_count')"],
        address: Annotated[str, "Blockchain address (if data_type is 'address_balance')"] = None,
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"] = None,
        look_back_days: Annotated[int, "how many days to look back"] = None,
    ) -> str:
        """
        Fetches various types of blockchain data. This is a placeholder and needs
        to be implemented with actual API calls to services like BlockCypher or Blockchain.com.
        """
        return interface.get_blockchain_data(blockchain_id, data_type, address, curr_date, look_back_days)




    @staticmethod
    @tool
    def get_simfin_balance_sheet(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent balance sheet of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
            str: a report of the company's most recent balance sheet
        """

        data_balance_sheet = interface.get_simfin_balance_sheet(ticker, freq, curr_date)

        return data_balance_sheet

    @staticmethod
    @tool
    def get_simfin_cashflow(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent cash flow statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent cash flow statement
        """

        data_cashflow = interface.get_simfin_cashflow(ticker, freq, curr_date)

        return data_cashflow

    @staticmethod
    @tool
    def get_simfin_income_stmt(
        ticker: Annotated[str, "ticker symbol"],
        freq: Annotated[
            str,
            "reporting frequency of the company's financial history: annual/quarterly",
        ],
        curr_date: Annotated[str, "current date you are trading at, yyyy-mm-dd"],
    ):
        """
        Retrieve the most recent income statement of a company
        Args:
            ticker (str): ticker symbol of the company
            freq (str): reporting frequency of the company's financial history: annual / quarterly
            curr_date (str): current date you are trading at, yyyy-mm-dd
        Returns:
                str: a report of the company's most recent income statement
        """

        data_income_stmt = interface.get_simfin_income_statements(
            ticker, freq, curr_date
        )

        return data_income_stmt

    @staticmethod
    @tool
    def get_google_news(
        query: Annotated[str, "Query to search with"],
        curr_date: Annotated[str, "Curr date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news from Google News based on a query and date range.
        Args:
            query (str): Query to search with
            curr_date (str): Current date in yyyy-mm-dd format
            look_back_days (int): How many days to look back
        Returns:
            str: A formatted string containing the latest news from Google News based on the query and date range.
        """

        google_news_results = interface.get_google_news(query, curr_date, 3)

        return google_news_results

    @staticmethod
    @tool
    def get_stock_news_llm(
        ticker: Annotated[str, "The cryptocurrency symbol (e.g., 'BTC', 'ETH')"], # Updated annotation
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest news about a given cryptocurrency by using the configured LLM's news API. # Updated description
        Args:
            ticker (str): Cryptocurrency symbol. e.g. BTC, ETH
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest news about the cryptocurrency on the given date.
        """

        llm_news_results = interface.get_stock_news_llm(ticker, curr_date)

        return llm_news_results

    @staticmethod
    @tool
    def get_global_news_llm(
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest macroeconomics news on a given date using the configured LLM's macroeconomics news API.
        Args:
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest macroeconomic news on the given date.
        """

        llm_news_results = interface.get_global_news_llm(curr_date)

        return llm_news_results

    @staticmethod
    @tool
    def get_fundamentals_llm(
        ticker: Annotated[str, "The cryptocurrency symbol (e.g., 'BTC', 'ETH')"], # Updated annotation
        curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    ):
        """
        Retrieve the latest fundamental information about a given cryptocurrency on a given date by using the configured LLM's API. # Updated description
        Args:
            ticker (str): Cryptocurrency symbol. e.g. BTC, ETH
            curr_date (str): Current date in yyyy-mm-dd format
        Returns:
            str: A formatted string containing the latest fundamental information about the cryptocurrency on the given date.
        """

        llm_fundamentals_results = interface.get_fundamentals_llm(
            ticker, curr_date
        )

        return llm_fundamentals_results

    @staticmethod
    @tool
    def summarize_text(
        text: Annotated[str, "The text to summarize"],
        max_length: Annotated[int, "Maximum length of the summary in characters"] = 1500,
    ) -> str:
        """
        Summarizes a given text to a specified maximum length.
        Args:
            text (str): The text content to be summarized.
            max_length (int): The maximum desired length of the summary in characters.
        Returns:
            str: The summarized text.
        """
        config = Toolkit._config  # Access class-level config
        llm_provider = config["llm_provider"].lower()
        backend_url = config["backend_url"]
        quick_think_llm = config["quick_think_llm"]
        llm_timeout = config.get("llm_timeout")
        proxies = config.get("proxies")

        prompt_text = f"Summarize the following text concisely, keeping it under {max_length} characters:\n\n{text}"

        if llm_provider == "google":
            client = ChatGoogleGenerativeAI(model=quick_think_llm, timeout=llm_timeout)
            response = client.invoke(prompt_text)
            summary = response.content
        elif llm_provider == "openai" or llm_provider == "ollama" or llm_provider == "openrouter":
            if proxies:
                client = OpenAI(base_url=backend_url, http_client=httpx.Client(proxies=proxies))
            else:
                client = OpenAI(base_url=backend_url)
            
            response = client.responses.create(
                model=quick_think_llm,
                input=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt_text,
                            }
                        ],
                    }
                ],
                text={"format": {"type": "text"}},
                reasoning={},
                temperature=0.7,
                max_output_tokens=max_length, # Use max_length for output tokens
                top_p=1,
                store=True,
            )
            summary = response.output[1].content[0].text
        else:
            raise ValueError(f"Unsupported LLM provider for summarization: {llm_provider}")
        
        # Ensure the summary does not exceed max_length
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
            
        return summary
