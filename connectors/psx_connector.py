"""
Pakistan Stock Exchange data connector.

This uses Yahoo Finance tickers for PSX listings, which usually end in .KA
for Karachi, e.g. HBL.KA, OGDC.KA, LUCK.KA.
"""

import pandas as pd
import yfinance as yf

from core.signal_universe import configured_psx_symbols
from legacy_config import PSX_INTERVAL, PSX_PERIOD


def get_psx_symbols() -> list[str]:
    """Return the full configured PSX universe from signal_universe.yaml."""
    return configured_psx_symbols()


def fetch_psx_ohlcv_df(
    symbol: str, period: str = PSX_PERIOD, interval: str = PSX_INTERVAL
) -> pd.DataFrame:
    """Returns a DataFrame with columns: timestamp, open, high, low, close, volume."""
    df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
    if df.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.reset_index()
    date_col = "Date" if "Date" in df.columns else "Datetime"
    df = df.rename(
        columns={
            date_col: "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    return df[["timestamp", "open", "high", "low", "close", "volume"]].dropna()
