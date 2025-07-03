import pandas as pd
from stockstats import wrap
from typing import Annotated
import os
from .config import get_config
from datetime import datetime # Add datetime import for consistency


class StockstatsUtils:
    @staticmethod
    def get_stock_stats(
        symbol: Annotated[str, "The symbol (e.g., 'BTC/USDT', 'AAPL')"],
        indicator: Annotated[
            str, "quantitative indicators based off of the stock data for the company"
        ],
        curr_date: Annotated[
            str, "curr date for retrieving stock price data, YYYY-mm-dd"
        ],
        data_dir: Annotated[
            str,
            "directory where the data is stored.",
        ],
        online: Annotated[
            bool,
            "whether to use online tools to fetch data or offline tools. If True, will use online tools.",
        ] = False,
    ):
        from tradingagents.dataflows.interface import get_crypto_ohlcv_data_window # Import here to avoid circular dependency

        df = None
        data = None
        is_crypto = "/" in symbol # Simple check for crypto symbol

        if is_crypto:
            # For cryptocurrency, fetch OHLCV data using crypto_utils
            # Assuming '1d' timeframe for daily indicators, adjust as needed
            ohlcv_df_str = get_crypto_ohlcv_data_window(
                exchange_id="binance", # Default to binance, can be made configurable
                symbol=symbol,
                timeframe="1d",
                curr_date=curr_date,
                look_back_days=365 # Fetch enough data for indicators (e.g., 200-day SMA)
            )
            if "No OHLCV data found" in ohlcv_df_str:
                return ""
            
            try:
                # Parse the string output back to DataFrame
                df_lines = ohlcv_df_str.split('\n')
                df_start_index = -1
                for i, line in enumerate(df_lines):
                    if line.strip().startswith('timestamp'):
                        df_start_index = i
                        break
                
                if df_start_index != -1:
                    df_content = "\n".join(df_lines[df_start_index:])
                    from io import StringIO
                    data = pd.read_csv(StringIO(df_content), index_col='timestamp', parse_dates=True, sep=r'\s\s+', engine='python')
                    data.columns = [col.lower() for col in data.columns] # Ensure lowercase column names
                else:
                    data = pd.DataFrame()
            except Exception as e:
                print(f"Error parsing crypto OHLCV data string in stockstats_utils: {e}")
                data = pd.DataFrame()

            if data.empty:
                return ""
            
            df = wrap(data)
            df["date"] = df.index.strftime("%Y-%m-%d") # Align column name for consistency
            curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
            curr_date_str = curr_date_dt.strftime("%Y-%m-%d")

        df[indicator]  # trigger stockstats to calculate the indicator
        
        # Always use 'date' column for crypto
        date_col = "date"
        
        matching_rows = df[df[date_col].str.startswith(curr_date_str)]

        if not matching_rows.empty:
            indicator_value = matching_rows[indicator].values[0]
            return indicator_value
        else:
            return "N/A: Not a trading day (weekend or holiday) or data not available"
