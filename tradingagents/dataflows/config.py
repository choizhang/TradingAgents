import tradingagents.default_config as default_config
from typing import Dict, Optional
import os
from dotenv import load_dotenv

# Use default config but allow it to be overridden
_config: Optional[Dict] = None
DATA_DIR: Optional[str] = None


def initialize_config():
    """Initialize the configuration with default values."""
    global _config, DATA_DIR
    if _config is None:
        load_dotenv() # Load environment variables from .env file
        _config = default_config.DEFAULT_CONFIG.copy()
        _config["finnhub_api_key"] = os.getenv("FINNHUB_API_KEY")
        _config["openai_api_key"] = os.getenv("OPENAI_API_KEY")
        _config["google_api_key"] = os.getenv("GOOGLE_API_KEY")
        DATA_DIR = _config["data_dir"]


def set_config(config: Dict):
    """Update the configuration with custom values."""
    global _config, DATA_DIR
    if _config is None:
        _config = default_config.DEFAULT_CONFIG.copy()
    _config.update(config)
    DATA_DIR = _config["data_dir"]


def get_config() -> Dict:
    """Get the current configuration."""
    if _config is None:
        initialize_config()
    return _config.copy()


# Initialize with default config
initialize_config()
