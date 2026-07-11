"""
PMEX (Pakistan Mercantile Exchange) instrument loader for signal-only scans.

Supported instruments come from ``config/signal_universe.yaml``
(``signal_universe.pmex_instruments``). Live MT5 routing is not wired here;
OHLCV uses public commodity futures proxies for indicator/LLM analysis only.
"""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from core.signal_universe import configured_pmex_instruments
from models.common import ConfigurationError

# Display/instrument id → Yahoo continuous futures proxy (signal-only).
_PMEX_YAHOO_PROXIES: dict[str, str] = {
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "CRUDE_OIL": "CL=F",
    "BRENT": "BZ=F",
    "NATURAL_GAS": "NG=F",
    "COPPER": "HG=F",
    "COTTON": "CT=F",
}

_PMEX_PERIOD = "6mo"
_PMEX_INTERVAL = "1d"


def get_pmex_instruments() -> list[str]:
    """Return every supported PMEX instrument from configuration (no truncation)."""
    instruments = configured_pmex_instruments()
    unknown = [item for item in instruments if item not in _PMEX_YAHOO_PROXIES]
    if unknown:
        raise ConfigurationError(
            "Unsupported PMEX instrument(s) in signal_universe.pmex_instruments: "
            + ", ".join(unknown)
        )
    return list(instruments)


def yahoo_symbol_for_pmex(instrument: str) -> str:
    """Map a PMEX instrument id to its Yahoo proxy ticker."""
    key = instrument.strip().upper().replace(" ", "_").replace("-", "_")
    proxy = _PMEX_YAHOO_PROXIES.get(key)
    if proxy is None:
        raise ConfigurationError(f"No Yahoo proxy configured for PMEX instrument: {instrument!r}")
    return proxy


def fetch_pmex_ohlcv_df(
    instrument: str,
    *,
    period: str = _PMEX_PERIOD,
    interval: str = _PMEX_INTERVAL,
) -> pd.DataFrame:
    """Return OHLCV for a PMEX instrument via its commodity futures proxy."""
    ticker = yahoo_symbol_for_pmex(instrument)
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=False)
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
