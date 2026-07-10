"""
Binance data connector using ccxt.

Signal-only mode by default (see config.SIGNAL_ONLY) — this file only
READS market data. No order-placing code is wired up here on purpose;
that's a separate, deliberate step once you trust the signals.
"""

import ccxt
import pandas as pd
from config import EXCHANGE_ID, QUOTE_CURRENCY, TOP_N, TIMEFRAME, CANDLE_LOOKBACK


def get_exchange():
    exchange_class = getattr(ccxt, EXCHANGE_ID)
    return exchange_class({"enableRateLimit": True})


def get_top_n_symbols(exchange, n: int = TOP_N, quote: str = QUOTE_CURRENCY) -> list[str]:
    """Top N symbols by 24h quote volume, e.g. ['BTC/USDT', 'ETH/USDT', ...].
    Filters out leveraged tokens (UP/DOWN/BULL/BEAR) which distort rankings."""
    markets = exchange.load_markets()
    tickers = exchange.fetch_tickers()

    candidates = []
    for symbol, market in markets.items():
        if not market.get("active"):
            continue
        if market.get("quote") != quote:
            continue
        if market.get("type") != "spot":
            continue
        base = market.get("base", "")
        if any(tag in base for tag in ("UP", "DOWN", "BULL", "BEAR")):
            continue
        ticker = tickers.get(symbol)
        if not ticker or ticker.get("quoteVolume") is None:
            continue
        candidates.append((symbol, ticker["quoteVolume"]))

    candidates.sort(key=lambda x: x[1], reverse=True)
    return [sym for sym, _ in candidates[:n]]


def fetch_ohlcv_df(
    exchange, symbol: str, timeframe: str = TIMEFRAME, limit: int = CANDLE_LOOKBACK
) -> pd.DataFrame:
    """Returns a DataFrame with columns: timestamp, open, high, low, close, volume."""
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return df
