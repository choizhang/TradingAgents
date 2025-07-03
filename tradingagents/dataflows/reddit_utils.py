import requests
import time
import json
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Annotated
import os
import re

def fetch_top_from_category(
    category: Annotated[
        str, "Category to fetch top post from. Collection of subreddits."
    ],
    date: Annotated[str, "Date to fetch top posts from."],
    max_limit: Annotated[int, "Maximum number of posts to fetch."],
    query: Annotated[str, "Optional query to search for in the subreddit."] = None,
    data_path: Annotated[
        str,
        "Path to the data folder. Default is 'reddit_data'.",
    ] = "reddit_data",
):
    base_path = data_path
    all_content = []
    
    crypto_symbols = ["BTC", "ETH", "XRP", "LTC", "BCH", "DOGE", "ADA", "SOL", "DOT", "LINK"] # Extend as needed

    target_files = []
    category_path = os.path.join(base_path, category)

    if category == "company_news" and query and query.upper() in crypto_symbols:
        # Try to find a specific crypto data file
        specific_file_name = f"{query.upper()}.jsonl"
        specific_file_path = os.path.join(category_path, specific_file_name)
        if os.path.exists(specific_file_path):
            target_files.append(specific_file_name)
            print(f"Targeting specific crypto data file: {specific_file_path}")
        else:
            print(f"Specific crypto data file not found: {specific_file_path}. Falling back to general search in category.")
            # Fallback to listing all files in the category
            # If specific crypto data file not found, return empty list as we are not caching locally
            return []
    else:
        # For other categories or non-crypto queries, if local files are not expected, return empty
        return []

    # Since we are not reading from local files, and not fetching from API,
    # we will simply return an empty list for now.
    return []
