import ccxt
from typing import Annotated, Dict
from datetime import datetime, timedelta
import pandas as pd
import os
import json
from tqdm import tqdm
from .config import DATA_DIR, get_config # Import get_config
import stockstats # Import stockstats

class CryptoUtils:
    def __init__(self):
        self.exchanges = {} # Cache exchange instances
        self.config = get_config() # Get the global config

    def _get_exchange(self, exchange_id: str):
        if exchange_id not in self.exchanges:
            try:
                exchange_class = getattr(ccxt, exchange_id)
                exchange_options = {
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'spot', # Explicitly set default type to spot
                    }
                }
                # Add proxy settings if available in config
                if self.config.get("proxies"):
                    exchange_options['proxies'] = self.config["proxies"]

                exchange = exchange_class(exchange_options)
                exchange.load_markets() # Attempt to load markets to check connectivity
                self.exchanges[exchange_id] = exchange
            except (ccxt.NetworkError, ccxt.ExchangeNotAvailable, ccxt.RequestTimeout) as e:
                print(f"网络或交易所连接错误 '{exchange_id}': {e}")
                # 尝试备用交易所：Coinbase 优先， Kraken备选
                fallback_exchanges = ['coinbase', 'kraken']
                for fallback_id in fallback_exchanges:
                    if fallback_id == exchange_id: # Don't try the same exchange again
                        continue
                    print(f"尝试使用 '{fallback_id}' 作为备用交易所。")
                    try:
                        exchange_class = getattr(ccxt, fallback_id)
                        fallback_options = {
                            'enableRateLimit': True,
                            'options': {
                                'defaultType': 'spot',
                            }
                        }
                        if self.config.get("proxies"):
                            fallback_options['proxies'] = self.config["proxies"]

                        exchange = exchange_class(fallback_options)
                        exchange.load_markets() # 尝试加载市场以检查连接性
                        self.exchanges[fallback_id] = exchange
                        print(f"成功连接到 {fallback_id} 交易所。")
                        return self.exchanges[fallback_id]
                    except Exception as fallback_e:
                        print(f"备用交易所 '{fallback_id}' 未能初始化或连接: {fallback_e}")
                raise ValueError(f"所有尝试的交易所（包括备用）都未能初始化或连接。原始错误: {e}")
            except Exception as e:
                raise ValueError(f"初始化或连接交易所 '{exchange_id}' 时发生未知错误: {e}")
        return self.exchanges[exchange_id]

    def _standardize_symbol(self, exchange, symbol: str) -> str:
        """Standardize the trading pair symbol for the given exchange."""
        if symbol in exchange.symbols:
            return symbol
        # Try to find a matching symbol by iterating through available symbols
        for s in exchange.symbols:
            if s.replace('/', '').lower() == symbol.replace('/', '').lower():
                return s
            # Special handling for Kraken's XBT/USD vs BTC/USD
            if exchange.id == 'kraken':
                if symbol.upper() == 'BTC/USDT' and 'XBT/USDT' in exchange.symbols:
                    return 'XBT/USDT'
                if symbol.upper() == 'BTC/USD' and 'XBT/USD' in exchange.symbols:
                    return 'XBT/USD'
                if symbol.upper() == 'BTC/EUR' and 'XBT/EUR' in exchange.symbols:
                    return 'XBT/EUR'
        raise ValueError(f"Symbol '{symbol}' not found on exchange '{exchange.id}' or could not be standardized.")

    def get_ohlcv_data(
        self,
        exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
        symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
        timeframe: Annotated[str, "The OHLCV timeframe (e.g., '1m', '5m', '1h', '1d')"],
        since_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        limit: Annotated[int, "Number of data points to fetch"],
    ) -> pd.DataFrame:
        """
        Fetches OHLCV (Open, High, Low, Close, Volume) data for a given cryptocurrency pair.
        """
        exchange = self._get_exchange(exchange_id)
        standardized_symbol = self._standardize_symbol(exchange, symbol)
        since_timestamp = exchange.parse8601(since_date + 'T00:00:00Z')

        ohlcv = exchange.fetch_ohlcv(standardized_symbol, timeframe, since_timestamp, limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    def get_current_price(
        self,
        exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
        symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
    ) -> float:
        """
        Fetches the current price of a cryptocurrency pair.
        """
        exchange = self._get_exchange(exchange_id)
        standardized_symbol = self._standardize_symbol(exchange, symbol)
        ticker = exchange.fetch_ticker(standardized_symbol)
        return ticker['last']

    def get_order_book(
        self,
        exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
        symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
        limit: Annotated[int, "Number of bids and asks to fetch"],
    ) -> Dict:
        """
        Fetches the order book for a given cryptocurrency pair.
        """
        exchange = self._get_exchange(exchange_id)
        standardized_symbol = self._standardize_symbol(exchange, symbol)
        order_book = exchange.fetch_order_book(standardized_symbol, limit)
        return order_book

    def get_historical_ohlcv_data_in_range(
        self,
        exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
        symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
        timeframe: Annotated[str, "The OHLCV timeframe (e.g., '1m', '5m', '1h', '1d')"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> pd.DataFrame:
        """
        Fetches historical OHLCV data for a given cryptocurrency pair within a date range.
        Data is cached locally.
        """
        cache_dir = os.path.join(DATA_DIR, "market_data", "crypto_price_data")
        os.makedirs(cache_dir, exist_ok=True)
        file_path = os.path.join(cache_dir, f"{exchange_id}-{symbol.replace('/', '')}-{timeframe}.csv")

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        all_ohlcv = []
        current_dt = start_dt
        exchange = self._get_exchange(exchange_id)
        standardized_symbol = self._standardize_symbol(exchange, symbol)

        # Load existing data from cache if available
        if os.path.exists(file_path):
            cached_df = pd.read_csv(file_path, index_col='timestamp', parse_dates=True)
            # Filter out data that is already within the requested range
            cached_df = cached_df[(cached_df.index >= start_dt) & (cached_df.index <= end_dt)]
            all_ohlcv.append(cached_df)
            # Adjust current_dt to fetch data after the latest cached date
            if not cached_df.empty:
                current_dt = cached_df.index.max().to_pydatetime() + timedelta(days=1)
                if current_dt > end_dt: # All data already cached
                    return pd.concat(all_ohlcv).sort_index() if all_ohlcv else pd.DataFrame()

        # Fetch new data in chunks
        while current_dt <= end_dt:
            since_timestamp = exchange.parse8601(current_dt.strftime("%Y-%m-%dT00:00:00Z"))
            try:
                # Fetching 1000 data points at a time (adjust limit as needed)
                ohlcv_chunk = exchange.fetch_ohlcv(standardized_symbol, timeframe, since_timestamp, 1000)
                if not ohlcv_chunk:
                    break
                
                df_chunk = pd.DataFrame(ohlcv_chunk, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df_chunk['timestamp'] = pd.to_datetime(df_chunk['timestamp'], unit='ms')
                df_chunk.set_index('timestamp', inplace=True)
                
                # Filter to ensure data is within the requested end_date
                df_chunk = df_chunk[df_chunk.index <= end_dt]
                
                all_ohlcv.append(df_chunk)
                
                # Move to the next period
                last_timestamp_in_chunk = df_chunk.index.max().to_pydatetime()
                if timeframe == '1d':
                    current_dt = last_timestamp_in_chunk + timedelta(days=1)
                elif timeframe == '1h':
                    current_dt = last_timestamp_in_chunk + timedelta(hours=1)
                # Add more timeframe logic if needed
                else: # Default to daily if timeframe is not explicitly handled
                    current_dt = last_timestamp_in_chunk + timedelta(days=1)

                # Break if the last fetched timestamp is already past the end_dt
                if last_timestamp_in_chunk >= end_dt:
                    break

            except Exception as e:
                print(f"Error fetching OHLCV data for {standardized_symbol} from {exchange_id}: {e}")
                break
        
        final_df = pd.concat(all_ohlcv).sort_index().drop_duplicates() if all_ohlcv else pd.DataFrame()
        
        # Save to cache
        if not final_df.empty:
            final_df.to_csv(file_path)

        return final_df

    def get_technical_indicators(
        self,
        exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
        symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
        timeframe: Annotated[str, "The OHLCV timeframe (e.g., '1m', '5m', '1h', '1d')"],
        start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
        end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    ) -> pd.DataFrame:
        """
        Fetches OHLCV data and calculates technical indicators using stockstats.
        """
        df = self.get_historical_ohlcv_data_in_range(exchange_id, symbol, timeframe, start_date, end_date)
        if df.empty:
            return pd.DataFrame()

        # Ensure column names are lowercase for stockstats
        df.columns = df.columns.str.lower()

        # Calculate technical indicators
        stock = stockstats.StockDataFrame.retype(df)
        # Example indicators, add more as needed
        stock["macd"]
        stock["macds"]
        stock["macdh"]
        stock["rsi_6"]
        stock["rsi_12"]
        stock["kdjk"]
        stock["kdjd"]
        stock["kdjj"]
        stock["boll"]
        stock["boll_ub"]
        stock["boll_lb"]
        stock["close_20_sma"]
        stock["close_50_sma"]
        stock["close_200_sma"]

        return stock

crypto_utils = CryptoUtils()

def get_crypto_ohlcv_data_window(
    exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
    symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
    timeframe: Annotated[str, "The OHLCV timeframe (e.g., '1m', '5m', '1h', '1d')"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
    look_back_days: Annotated[int, "how many days to look back"],
) -> str:
    """
    Retrieve OHLCV data for a cryptocurrency pair within a time frame from local cache or online.
    """
    start_date = datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=look_back_days)
    start_date_str = start_date.strftime("%Y-%m-%d")

    df = crypto_utils.get_historical_ohlcv_data_in_range(
        exchange_id, symbol, timeframe, start_date_str, curr_date
    )

    if df.empty:
        return f"No OHLCV data found for {symbol} on {exchange_id} from {start_date_str} to {curr_date}."

    with pd.option_context(
        "display.max_rows", None, "display.max_columns", None, "display.width", None
    ):
        df_string = df.to_string()

    return (
        f"## Raw Crypto OHLCV Data for {symbol} from {start_date_str} to {curr_date} on {exchange_id}:\n\n"
        + df_string
    )

def get_crypto_current_price(
    exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
    symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
) -> str:
    """
    Retrieve the current price of a cryptocurrency pair.
    """
    try:
        price = crypto_utils.get_current_price(exchange_id, symbol)
        return f"Current price of {symbol} on {exchange_id}: {price}"
    except Exception as e:
        return f"Error getting current price for {symbol} on {exchange_id}: {e}"

def get_crypto_order_book(
    exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'binance', 'coinbasepro')"],
    symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
    limit: Annotated[int, "Number of bids and asks to fetch"],
) -> str:
    """
    Retrieve the order book for a cryptocurrency pair.
    """
    try:
        order_book = crypto_utils.get_order_book(exchange_id, symbol, limit)
        return f"Order book for {symbol} on {exchange_id}:\nBids: {order_book['bids']}\nAsks: {order_book['asks']}"
    except Exception as e:
        return f"Error getting order book for {symbol} on {exchange_id}: {e}"

# Placeholder for blockchain data (e.g., BlockCypher, Blockchain.com)
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
    return f"Blockchain data for {blockchain_id}, type {data_type} is not yet implemented."

def get_crypto_technical_indicators_data(
   symbol: Annotated[str, "The trading pair symbol (e.g., 'BTC/USDT', 'ETH/USD')"],
   curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
   look_back_days: Annotated[int, "how many days to look back"],
   exchange_id: Annotated[str, "The ID of the cryptocurrency exchange (e.g., 'kraken', 'coinbasepro')"] = "kraken",
   timeframe: Annotated[str, "The OHLCV timeframe (e.g., '1d')"] = "1d",
) -> pd.DataFrame:
   """
   Retrieve technical indicators for a given cryptocurrency.
   """
   start_date = datetime.strptime(curr_date, "%Y-%m-%d") - timedelta(days=look_back_days)
   start_date_str = start_date.strftime("%Y-%m-%d")

   df = crypto_utils.get_technical_indicators(
       exchange_id, symbol, timeframe, start_date_str, curr_date
   )
   return df