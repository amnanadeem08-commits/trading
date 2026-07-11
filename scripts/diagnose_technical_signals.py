"""Diagnose technical-rule signals for Crypto/PSX/PMEX (LLM rate-limit path)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

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

_SEED = ROOT / "scripts" / "seed_production_workbook_technical.py"
_spec = importlib.util.spec_from_file_location("seed_prod_tech", _SEED)
assert _spec and _spec.loader
_seed_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_seed_mod)
_signal_from_technicals = _seed_mod._signal_from_technicals
RSI_BUY_HARD = _seed_mod.RSI_BUY_HARD
RSI_SELL_HARD = _seed_mod.RSI_SELL_HARD
RSI_BUY_SOFT = _seed_mod.RSI_BUY_SOFT
RSI_SELL_SOFT = _seed_mod.RSI_SELL_SOFT


def _probe_llm() -> tuple[str, bool]:
    try:
        from core.llm_analyzer import assert_ai_ready

        assert_ai_ready(verify_remote=True)
        return "available", True
    except Exception as exc:
        msg = str(exc).lower()
        if "429" in msg or "rate" in msg:
            return "rate_limited", False
        return f"unavailable:{type(exc).__name__}", False


def _gates(rsi: float, hist: float, crossover: str) -> tuple[bool, bool]:
    buy = rsi < RSI_BUY_HARD or crossover == "bullish" or (rsi < RSI_BUY_SOFT and hist > 0)
    sell = rsi > RSI_SELL_HARD or crossover == "bearish" or (rsi > RSI_SELL_SOFT and hist < 0)
    return buy, sell


def _trace(market: str, symbol: str, fetch, *, llm_status: str) -> dict:
    print("\n" + "=" * 64)
    print(f"{market.upper()}  {symbol}")
    print("=" * 64)

    out: dict = {
        "market": market,
        "symbol": symbol,
        "llm_status": llm_status,
        "llm_used": False,
        "signal_source": "technical_rules",
    }

    try:
        df = fetch(symbol)
        if len(df) < 30:
            print("Market Data: FAIL — not enough candles")
            print("Indicators: SKIP")
            print("Technical Rule Signal: SKIP")
            print(f"LLM Status: {llm_status}")
            print("Final Signal: SKIP")
            out["final"] = None
            out["skip_reason"] = "insufficient_history"
            return out
        print(
            "Market Data: PASS "
            f"(rows={len(df)}, last_close={float(df['close'].iloc[-1]):.6g})"
        )
    except Exception as exc:
        print(f"Market Data: FAIL — {exc}")
        out["final"] = None
        out["skip_reason"] = str(exc)
        return out

    technicals = summarize_technical(df)
    rsi = float(technicals["rsi"])
    hist = float(technicals["macd_histogram"])
    xover = str(technicals.get("macd_crossover") or "none")
    print(
        "Indicators: PASS "
        f"(rsi={rsi}, macd_hist={hist}, crossover={xover}, "
        f"vol={technicals['volatility_pct']})"
    )

    buy_gate, sell_gate = _gates(rsi, hist, xover)
    print(f"Technical Rule gates: BUY={buy_gate} SELL={sell_gate}")

    row = _signal_from_technicals(symbol, technicals, llm_status=llm_status)
    tech_signal = row["signal"]
    print(f"Technical Rule Signal: {tech_signal} ({row['confidence']})")
    print(f"  reason: {row['reasoning']}")
    print(f"LLM Status: {row['llm_status']}")
    print(f"LLM used: {row['llm_used']}")
    print(
        f"Final Signal: {tech_signal}  "
        f"[signal_source={row['signal_source']} llm_used={row['llm_used']}]"
    )

    out.update(
        {
            "rsi": rsi,
            "macd_histogram": hist,
            "macd_crossover": xover,
            "buy_gate": buy_gate,
            "sell_gate": sell_gate,
            "technical_signal": tech_signal,
            "final": tech_signal,
            "confidence": row["confidence"],
            "signal_source": row["signal_source"],
            "llm_status": row["llm_status"],
            "llm_used": row["llm_used"],
        }
    )
    return out


def _summary(label: str, rows: list[dict]) -> None:
    finals = [r["final"] for r in rows if r.get("final")]
    buy = sum(1 for s in finals if s == "BUY")
    sell = sum(1 for s in finals if s == "SELL")
    hold = sum(1 for s in finals if s == "HOLD")
    print(f"\n{label} summary: BUY={buy} SELL={sell} HOLD={hold} (n={len(finals)})")


def main() -> int:
    probe_status, _llm_ok = _probe_llm()
    # This diagnosis exercises the rate-limit fallback path explicitly.
    llm_status = "rate_limited"
    print("=== SIGNAL GENERATION DIAGNOSIS (technical fallback) ===")
    print(f"llm_probe_status={probe_status}")
    print(f"fallback_llm_status={llm_status} llm_used=false signal_source=technical_rules")
    print(
        "Rule: BUY if "
        f"rsi<{RSI_BUY_HARD} OR bullish crossover OR (rsi<{RSI_BUY_SOFT} AND hist>0); "
        "SELL if "
        f"rsi>{RSI_SELL_HARD} OR bearish crossover OR (rsi>{RSI_SELL_SOFT} AND hist<0); "
        "else HOLD"
    )

    exchange = get_exchange()
    crypto_syms = configured_crypto_symbols()[:5]
    psx_syms = configured_psx_symbols()[:5]
    pmex_syms = configured_pmex_instruments()

    crypto_rows = [
        _trace(
            "crypto",
            s,
            lambda sym, ex=exchange: fetch_ohlcv_df(ex, sym),
            llm_status=llm_status,
        )
        for s in crypto_syms
    ]
    psx_rows = [
        _trace("psx", s, fetch_psx_ohlcv_df, llm_status=llm_status) for s in psx_syms
    ]
    pmex_rows = [
        _trace("pmex", s, fetch_pmex_ohlcv_df, llm_status=llm_status) for s in pmex_syms
    ]

    print("\n" + "=" * 64)
    print("SUMMARIES")
    print("=" * 64)
    _summary("Crypto", crypto_rows)
    _summary("PSX", psx_rows)
    _summary("PMEX", pmex_rows)

    all_rows = [r for r in crypto_rows + psx_rows + pmex_rows if r.get("final")]
    assert all(r.get("signal_source") == "technical_rules" for r in all_rows)
    assert all(r.get("llm_used") is False for r in all_rows)
    assert all(r.get("llm_status") == "rate_limited" for r in all_rows)

    finals = [r["final"] for r in all_rows]
    if finals and all(s == "HOLD" for s in finals):
        print("\nALL_HOLD_ROOT_CAUSE: technical rule still too strict after fix")
        print("DIAGNOSIS_NEEDS_FIX")
        return 2

    print("\nDIAGNOSIS_OK_DIRECTIONAL_PRESENT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
