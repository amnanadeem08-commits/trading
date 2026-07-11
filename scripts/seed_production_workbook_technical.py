"""Seed a production workbook when LLM providers are rate-limited.

Uses live OHLCV + RSI/MACD technicals. Writes only to outputs/production/
with generator=production_scan. Never uses proof wording or proof paths.

Technical rule (LLM-unavailable fallback):
  BUY  when RSI < 35, or bullish MACD crossover, or (RSI < 45 and hist > 0)
  SELL when RSI > 65, or bearish MACD crossover, or (RSI > 55 and hist < 0)
  HOLD only when none of the above fire (true neutrality / conflict).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from connectors.binance_connector import fetch_ohlcv_df, get_exchange  # noqa: E402
from connectors.pmex_connector import fetch_pmex_ohlcv_df  # noqa: E402
from connectors.psx_connector import fetch_psx_ohlcv_df  # noqa: E402
from core.indicators import summarize_technical  # noqa: E402
from core.signal_universe import (  # noqa: E402
    configured_crypto_symbols,
    configured_pmex_instruments,
    configured_psx_symbols,
)
from core.signal_workbook import PRODUCTION_GENERATOR, ensure_artifact_dirs  # noqa: E402
from main import save_results  # noqa: E402

# Explicit thresholds (kept here so diagnosis scripts can import/read them).
RSI_BUY_HARD = 35.0
RSI_SELL_HARD = 65.0
RSI_BUY_SOFT = 45.0
RSI_SELL_SOFT = 55.0


def _signal_from_technicals(
    symbol: str,
    technicals: dict,
    *,
    llm_status: str = "rate_limited",
) -> dict:
    """Map indicators → signal. HOLD only when the rule itself is neutral."""
    rsi = float(technicals["rsi"])
    hist = float(technicals["macd_histogram"])
    crossover = str(technicals.get("macd_crossover") or "none")

    if rsi < RSI_BUY_HARD or crossover == "bullish" or (rsi < RSI_BUY_SOFT and hist > 0):
        signal, confidence = "BUY", "medium"
        why = (
            f"BUY gate: rsi<{RSI_BUY_HARD}, bullish crossover, "
            f"or (rsi<{RSI_BUY_SOFT} and hist>0)"
        )
    elif rsi > RSI_SELL_HARD or crossover == "bearish" or (rsi > RSI_SELL_SOFT and hist < 0):
        signal, confidence = "SELL", "medium"
        why = (
            f"SELL gate: rsi>{RSI_SELL_HARD}, bearish crossover, "
            f"or (rsi>{RSI_SELL_SOFT} and hist<0)"
        )
    else:
        signal, confidence = "HOLD", "low"
        why = "No directional RSI/MACD gate fired (neutral/conflict)"

    return {
        "symbol": symbol,
        "signal": signal,
        "confidence": confidence,
        "reasoning": (
            f"Production technical scan for {symbol}: RSI={rsi}, "
            f"MACD_hist={hist}, crossover={crossover}. {why}."
        ),
        "fomo_fear_note": (
            "LLM unavailable or rate-limited; technical-rule fallback used."
            if llm_status == "rate_limited"
            else "Technical-rule path (LLM not used for this row)."
        ),
        "invalidation": "RSI cross back through 50 or MACD histogram flip.",
        "provider": "technical_rules",
        "model": "rsi_macd_fallback_v2",
        "signal_source": "technical_rules",
        "llm_status": llm_status,
        "llm_used": False,
    }


def _scan(market: str, symbols: list[str], fetch, *, llm_status: str) -> pd.DataFrame:
    rows = []
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] {market} {symbol}...")
        try:
            df = fetch(symbol)
            if len(df) < 30:
                print("  skipped: not enough history")
                continue
            technicals = summarize_technical(df)
            row = _signal_from_technicals(symbol, technicals, llm_status=llm_status)
            rows.append(row)
            print(
                f"  -> {row['signal']} "
                f"(source={row['signal_source']}, llm_used={row['llm_used']}, "
                f"llm_status={row['llm_status']})"
            )
        except Exception as exc:
            print(f"  error: {exc}")
        time.sleep(0.15)
    return pd.DataFrame(rows)


def main() -> int:
    ensure_artifact_dirs()
    exchange = get_exchange()
    llm_status = "rate_limited"  # this script is the explicit LLM-unavailable path

    crypto = _scan(
        "crypto",
        configured_crypto_symbols(),
        lambda symbol: fetch_ohlcv_df(exchange, symbol),
        llm_status=llm_status,
    )
    psx = _scan(
        "psx",
        configured_psx_symbols(),
        fetch_psx_ohlcv_df,
        llm_status=llm_status,
    )
    pmex = _scan(
        "pmex",
        configured_pmex_instruments(),
        fetch_pmex_ohlcv_df,
        llm_status=llm_status,
    )

    out = save_results(
        {"crypto": crypto, "psx": psx, "pmex": pmex},
        "all",
        generator=PRODUCTION_GENERATOR,
        source="scripts/seed_production_workbook_technical.py",
    )
    print("seeded_production_workbook=", out)
    for name, df in (("Crypto", crypto), ("PSX", psx), ("PMEX", pmex)):
        if df.empty:
            print(f"{name}: BUY=0 SELL=0 HOLD=0")
            continue
        counts = df["signal"].value_counts().to_dict()
        print(
            f"{name}: BUY={counts.get('BUY', 0)} "
            f"SELL={counts.get('SELL', 0)} HOLD={counts.get('HOLD', 0)}"
        )
    assert not any(
        str(r).startswith("Proof scan for")
        for df in (crypto, psx, pmex)
        for r in (df["reasoning"].tolist() if not df.empty else [])
    )
    assert (crypto["llm_used"] == False).all() if not crypto.empty else True  # noqa: E712
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
