"""
Pure-pandas technical indicators. No external TA library needed,
so there's nothing hidden — you can read exactly what's being computed.
"""

import pandas as pd
import numpy as np


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Relative Strength Index. Values 0-100.
    >70 = overbought territory, <30 = oversold territory (classic reading)."""
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # neutral fill for the warm-up period


def compute_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
    """Returns (macd_line, signal_line, histogram)."""
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_volatility(df: pd.DataFrame, period: int = 14) -> float:
    """Annualized-ish rolling volatility from close-to-close returns, as a %."""
    returns = df["close"].pct_change()
    return float(returns.rolling(period).std().iloc[-1] * 100)


def candle_summary(df: pd.DataFrame, n: int = 5) -> str:
    """Plain-English description of the last n candles, for feeding to the LLM.
    Keeps the LLM prompt compact instead of dumping raw OHLCV numbers."""
    recent = df.tail(n)
    lines = []
    for _, row in recent.iterrows():
        direction = "green" if row["close"] >= row["open"] else "red"
        body_pct = abs(row["close"] - row["open"]) / row["open"] * 100
        wick_upper = row["high"] - max(row["close"], row["open"])
        wick_lower = min(row["close"], row["open"]) - row["low"]
        lines.append(
            f"{direction} candle, body {body_pct:.2f}%, "
            f"upper wick {wick_upper:.4f}, lower wick {wick_lower:.4f}"
        )
    return "; ".join(lines)


def summarize_technical(df: pd.DataFrame) -> dict:
    """One-shot bundle of everything indicators.py knows about a symbol,
    ready to hand to the LLM prompt builder."""
    rsi = compute_rsi(df, period=14)
    macd_line, signal_line, hist = compute_macd(df)

    return {
        "last_close": float(df["close"].iloc[-1]),
        "rsi": round(float(rsi.iloc[-1]), 2),
        "rsi_trend": "rising" if rsi.iloc[-1] > rsi.iloc[-3] else "falling",
        "macd": round(float(macd_line.iloc[-1]), 6),
        "macd_signal": round(float(signal_line.iloc[-1]), 6),
        "macd_histogram": round(float(hist.iloc[-1]), 6),
        "macd_crossover": (
            "bullish"
            if hist.iloc[-1] > 0 and hist.iloc[-2] <= 0
            else "bearish" if hist.iloc[-1] < 0 and hist.iloc[-2] >= 0 else "none"
        ),
        "volatility_pct": round(compute_volatility(df), 3),
        "price_change_24_candles_pct": (
            round((df["close"].iloc[-1] / df["close"].iloc[-25] - 1) * 100, 2)
            if len(df) > 25
            else None
        ),
        "recent_candles": candle_summary(df),
    }
