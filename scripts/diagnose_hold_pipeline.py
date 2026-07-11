"""Diagnose HOLD assignment for one Crypto / PSX / PMEX symbol.

Does NOT change strategy. Prints stage-by-stage status for the live
main.py path (OHLCV → indicators → LLM → workbook row).

Strategy Engine / Risk Engine / Paper Risk Gate are NOT invoked by
scan_market(); they are reported as NOT_IN_PATH when absent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from connectors.binance_connector import fetch_ohlcv_df, get_exchange  # noqa: E402
from connectors.pmex_connector import fetch_pmex_ohlcv_df  # noqa: E402
from connectors.psx_connector import fetch_psx_ohlcv_df  # noqa: E402
from core.indicators import summarize_technical  # noqa: E402
from core.llm_analyzer import (  # noqa: E402
    assert_ai_ready,
    analyze,
    configured_provider,
    model_for_provider,
    print_startup_diagnostics,
    provider_status,
    startup_diagnostics,
)
from core.sentiment import fetch_fear_greed, interpret_for_prompt  # noqa: E402
from dashboard import latest_workbook, load_workbook  # noqa: E402
from main import get_market_context  # noqa: E402


ASSETS = (
    ("crypto", "BTC/USDT", fetch_ohlcv_df),
    ("psx", "MARI.KA", fetch_psx_ohlcv_df),
    ("pmex", "GOLD", fetch_pmex_ohlcv_df),
)


def _stage(name: str, status: str, input_data, output, reason: str) -> None:
    print(f"\n--- {name} ---")
    print(f"status: {status}")
    print(f"input:  {_short(input_data)}")
    print(f"output: {_short(output)}")
    print(f"reason: {reason}")


def _short(value, limit: int = 400) -> str:
    if isinstance(value, pd.DataFrame):
        return f"DataFrame(rows={len(value)}, cols={list(value.columns)})"
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _workbook_diagnosis() -> None:
    print("=== WORKBOOK CURRENTLY LOADED BY DASHBOARD ===")
    wb = latest_workbook()
    print(f"latest_workbook: {wb}")
    if wb is None:
        print("No loadable workbook.")
        return
    sheets = load_workbook(wb)
    for market, df in sheets.items():
        signals = df["signal"].value_counts().to_dict() if "signal" in df.columns else {}
        sample = str(df.iloc[0].get("reasoning", "")) if len(df) else ""
        print(f"  {market}: rows={len(df)} signals={signals}")
        print(f"    sample_reasoning={sample[:160]}")
        if sample.startswith("Proof scan for"):
            print(
                "    HOLD_SOURCE: proof_universe_scan_path.py mocked analyze() "
                "(always returns HOLD). NOT a live LLM decision."
            )


def _trace_one(market: str, symbol: str, fetch_fn) -> dict:
    print("\n" + "=" * 72)
    print(f"TRACE: {symbol}  market={market}")
    print("=" * 72)

    meta = {
        "symbol": symbol,
        "market": market,
        "is_hold_fallback": False,
        "hold_reason": None,
        "fallback_source": None,
        "risk_gate_reasons": [],
        "llm_provider": None,
        "authentication_status": None,
        "indicator_count": None,
        "strategy_score": None,
        "confidence": None,
        "final_signal": None,
        "hold_component": None,
    }

    # --- Market Data ---
    try:
        if market == "crypto":
            exchange = get_exchange()
            df = fetch_fn(exchange, symbol)
        else:
            df = fetch_fn(symbol)
        if len(df) < 30:
            _stage(
                "Market Data",
                "FAIL",
                {"symbol": symbol},
                {"rows": len(df)},
                f"not enough candle history ({len(df)} < 30)",
            )
            meta["hold_component"] = "Market Data (skip — no signal row)"
            meta["hold_reason"] = "insufficient OHLCV"
            return meta
        _stage(
            "Market Data",
            "PASS",
            {"symbol": symbol, "fetcher": fetch_fn.__name__},
            {
                "rows": len(df),
                "last_close": float(df["close"].iloc[-1]),
                "last_ts": str(df["timestamp"].iloc[-1]) if "timestamp" in df.columns else None,
            },
            "enough history for indicators",
        )
    except Exception as exc:
        _stage("Market Data", "FAIL", {"symbol": symbol}, None, str(exc))
        meta["hold_component"] = "Market Data"
        meta["hold_reason"] = str(exc)
        return meta

    # --- Indicators ---
    try:
        technicals = summarize_technical(df)
        meta["indicator_count"] = len(technicals)
        _stage(
            "Indicators",
            "PASS",
            {"ohlcv_rows": len(df)},
            technicals,
            "summarize_technical() produced RSI/MACD/vol bundle",
        )
    except Exception as exc:
        _stage("Indicators", "FAIL", {"ohlcv_rows": len(df)}, None, str(exc))
        meta["hold_component"] = "Indicators"
        meta["hold_reason"] = str(exc)
        return meta

    # --- Strategy Engine (not in main.scan_market path) ---
    _stage(
        "Strategy Engine",
        "NOT_IN_PATH",
        {"expected": "signal_engine rules / RSI-MACD candidate"},
        None,
        "main.scan_market() does not call signal_engine; skips straight to LLM",
    )
    meta["strategy_score"] = None

    # --- AI / LLM ---
    try:
        provider = configured_provider()
        model = model_for_provider(provider)
        meta["llm_provider"] = f"{provider}/{model}"
        diag = startup_diagnostics()
        meta["authentication_status"] = (
            "OK" if diag.get("api_key_configured") == "YES" else "MISSING_KEY"
        )
        sentiment_note = get_market_context(market)
        signal = analyze(symbol, technicals, sentiment_note, market_name=market)
        meta["confidence"] = signal.get("confidence")
        meta["final_signal"] = signal.get("signal")
        reasoning = str(signal.get("reasoning", ""))
        is_proof = reasoning.startswith("Proof scan for")
        is_auth_fallback = "Analysis failed, defaulting to HOLD" in reasoning
        meta["is_hold_fallback"] = is_auth_fallback or is_proof
        if is_proof:
            meta["fallback_source"] = "proof_universe_scan_path._fake_analyze"
            meta["hold_reason"] = "mocked HOLD from proof script"
        elif is_auth_fallback:
            meta["fallback_source"] = "legacy auth→HOLD catch (should be removed)"
            meta["hold_reason"] = reasoning
        elif signal.get("signal") == "HOLD":
            meta["hold_component"] = "AI / LLM Analysis"
            meta["hold_reason"] = reasoning
            meta["fallback_source"] = None
            meta["is_hold_fallback"] = False
        _stage(
            "AI / LLM Analysis",
            "PASS",
            {
                "provider": provider,
                "model": model,
                "prompt_technicals_keys": list(technicals.keys()),
            },
            {
                "signal": signal.get("signal"),
                "confidence": signal.get("confidence"),
                "reasoning": reasoning,
                "provider": signal.get("provider"),
                "model": signal.get("model"),
            },
            (
                "LLM returned HOLD as its recommendation"
                if signal.get("signal") == "HOLD"
                else f"LLM returned {signal.get('signal')}"
            ),
        )
        if signal.get("signal") == "HOLD" and meta["hold_component"] is None:
            meta["hold_component"] = "AI / LLM Analysis"
    except Exception as exc:
        _stage("AI / LLM Analysis", "FAIL", {"provider": provider_status()}, None, str(exc))
        meta["authentication_status"] = f"FAIL: {exc}"
        meta["hold_component"] = "AI / LLM Analysis"
        meta["hold_reason"] = str(exc)
        meta["is_hold_fallback"] = False
        return meta

    # --- Risk Engine (not in path) ---
    _stage(
        "Risk Engine",
        "NOT_IN_PATH",
        {"expected": "risk.orchestration"},
        None,
        "main.scan_market() does not invoke Risk Engine before writing workbook rows",
    )
    meta["risk_gate_reasons"] = []

    # --- Paper Risk Gate (not in path) ---
    _stage(
        "Paper Risk Gate",
        "NOT_IN_PATH",
        {"expected": "paper_trading.authorize_fill"},
        None,
        "signal-only scan does not run paper fill authorization",
    )

    # --- Final ---
    final = meta["final_signal"]
    if final == "HOLD":
        reason = (
            f"HOLD assigned by {meta['hold_component']}: {meta['hold_reason']}"
            if meta["hold_component"]
            else f"HOLD: {meta['hold_reason']}"
        )
    else:
        reason = f"Final signal from LLM analyze(): {final}"
    _stage(
        "Final Signal",
        "HOLD" if final == "HOLD" else "DIRECTIONAL",
        {"workbook_row_fields": ["symbol", "signal", "confidence", "reasoning", "..."]},
        {"signal": final, "confidence": meta["confidence"]},
        reason,
    )

    print("\n### META ###")
    for key in (
        "is_hold_fallback",
        "hold_reason",
        "fallback_source",
        "risk_gate_reasons",
        "llm_provider",
        "authentication_status",
        "indicator_count",
        "strategy_score",
        "confidence",
        "hold_component",
        "final_signal",
    ):
        print(f"  {key}: {meta[key]}")

    # Compact one-liner like the user's example
    print("\n### COMPACT ###")
    print(symbol.replace("/", ""))
    print(f"Market data: PASS")
    print(f"Indicators: PASS")
    print(f"Strategy: NOT_IN_PATH")
    print(f"LLM: {final} (confidence={meta['confidence']})")
    print(f"Risk: NOT_IN_PATH")
    print(f"Paper Gate: NOT_IN_PATH")
    print(f"Final: {final}")
    if final == "HOLD":
        print(f"HOLD component: {meta['hold_component']}")
        print(f"HOLD reason: {meta['hold_reason']}")

    return meta


def main() -> int:
    print("=== HOLD PIPELINE DIAGNOSIS (no code changes) ===\n")
    _workbook_diagnosis()

    print("\n=== LIVE AI STARTUP ===")
    print_startup_diagnostics()
    try:
        assert_ai_ready(verify_remote=True)
        print("Authentication: OK\n")
        auth = "OK"
    except Exception as exc:
        print(f"Authentication: FAIL — {exc}\n")
        auth = f"FAIL: {exc}"

    results = []
    for market, symbol, fetch_fn in ASSETS:
        if market == "crypto":
            # bind exchange into closure handled inside _trace_one
            results.append(_trace_one(market, symbol, fetch_fn))
        else:
            results.append(_trace_one(market, symbol, fetch_fn))

    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)

    wb = latest_workbook()
    wb_reason = None
    if wb is not None:
        sheets = load_workbook(wb)
        sample = ""
        for df in sheets.values():
            if len(df):
                sample = str(df.iloc[0].get("reasoning", ""))
                break
        if sample.startswith("Proof scan for"):
            wb_reason = (
                "Dashboard workbook is signals_all_* from proof_universe_scan_path.py: "
                "_fake_analyze always returns HOLD. This is the FIRST and shared HOLD source "
                "for Crypto/PSX/PMEX in the UI."
            )

    if wb_reason:
        print(f"Crypto HOLD reason: {wb_reason}")
        print(f"PSX HOLD reason:    {wb_reason}")
        print(f"PMEX HOLD reason:   {wb_reason}")
        print("\nShared component: proof mock analyze → workbook → dashboard load")
        print("(Live LLM path below is independent of what the dashboard currently shows.)")
    else:
        for r in results:
            print(f"{r['market'].upper()} ({r['symbol']}) HOLD reason: {r.get('hold_reason') or r.get('final_signal')}")
            print(f"  component={r.get('hold_component')} final={r.get('final_signal')}")

    print("\nLive-path results (one asset each):")
    for r in results:
        print(
            f"  {r['symbol']}: final={r.get('final_signal')} "
            f"component={r.get('hold_component')} "
            f"confidence={r.get('confidence')} "
            f"auth={auth}"
        )

    print("\nDIAGNOSIS_COMPLETE — no fix applied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
