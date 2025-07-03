import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data")), # Set data_dir to a 'data' folder in the project root
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data")), # Use the new data_dir for cache
        "dataflows/data_cache",
    ),
    # API Keys (will be overridden by environment variables if set)
    "finnhub_api_key": None,
    "openai_api_key": None,
    "google_api_key": None,
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://api.openai.com/v1",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # LLM Timeout
    "llm_timeout": 1200, # Default to 20 minutes
    # Tool settings
    "online_tools": True,
    # Proxy settings
    "proxies": None, # Can be a dictionary like {"http": "http://proxy.example.com", "https": "http://proxy.example.com"}
    # Crypto settings
    "default_crypto_pair": "BTC/USDT", # Default cryptocurrency trading pair
}
