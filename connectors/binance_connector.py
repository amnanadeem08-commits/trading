"""
Binance data connector using ccxt.

Signal-only mode by default (see config.SIGNAL_ONLY) — this file only
READS market data. No order-placing code is wired up here on purpose;
that's a separate, deliberate step once you trust the signals.
"""

import ccxt
import pandas as pd

from legacy_config import CANDLE_LOOKBACK, EXCHANGE_ID, TIMEFRAME


def get_exchange():
    exchange_class = getattr(ccxt, EXCHANGE_ID)
    return exchange_class({"enableRateLimit": True})


def fetch_ohlcv_df(
    exchange, symbol: str, timeframe: str = TIMEFRAME, limit: int = CANDLE_LOOKBACK
) -> pd.DataFrame:
    """Returns a DataFrame with columns: timestamp, open, high, low, close, volume."""
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df
