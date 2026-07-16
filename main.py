"""
Run this to scan Binance/USDT crypto pairs, Pakistan Stock Exchange symbols,
PMEX instruments, or combined markets in one Excel workbook.

SIGNAL-ONLY MODE: this prints/saves recommendations. It does NOT place
trades. That's deliberate - read the README before wiring up execution.

Usage:
    python main.py
    python main.py --market all
    python main.py --market both
    python main.py --market psx
    python main.py --market crypto
    python main.py --market pmex
"""

from __future__ import annotations

import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from connectors.binance_connector import fetch_ohlcv_df, get_exchange
from connectors.pmex_connector import fetch_pmex_ohlcv_df, get_pmex_instruments
from connectors.psx_connector import fetch_psx_ohlcv_df
from core.indicators import summarize_technical
from core.llm_analyzer import (
    AIAuthenticationError,
    AIConfigurationError,
    AIExecutionError,
    analyze,
    assert_ai_ready,
    print_startup_diagnostics,
)
from core.sentiment import fetch_fear_greed, interpret_for_prompt
from core.signal_universe import configured_crypto_symbols, configured_psx_symbols
from core.signal_workbook import (
    PRODUCTION_GENERATOR,
    ensure_artifact_dirs,
    output_dir_for_generator,
    write_meta_sheet,
)
from legacy_config import MARKET, SIGNAL_ONLY

if TYPE_CHECKING:
    from collections.abc import Sequence

MARKET_SHEETS = {
    "psx": "PSX",
    "crypto": "Crypto",
    "pmex": "PMEX",
}

_MARKET_CHOICES = ("crypto", "psx", "pmex", "both", "all")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan crypto, PSX, PMEX, or combined markets for LLM trade signals."
    )
    parser.add_argument(
        "--market",
        choices=list(_MARKET_CHOICES),
        default=MARKET,
        help="Market to scan: crypto, psx, pmex, both (crypto+PSX), or all.",
    )
    return parser.parse_args()


def markets_to_run(market: str) -> list[str]:
    market = market.lower()
    if market == "both":
        return ["psx", "crypto"]
    if market in {"all", "all_markets"}:
        return ["psx", "crypto", "pmex"]
    return [market]


def get_market_context(market: str) -> str:
    if market == "crypto":
        print("Fetching market-wide crypto sentiment...")
        fg = fetch_fear_greed()
        sentiment_note = interpret_for_prompt(fg)
        print(f"  {sentiment_note}\n")
        return sentiment_note

    if market == "pmex":
        note = (
            "PMEX commodities context: futures/margin instruments. "
            "Technicals use public commodity futures proxies until MT5 live feed is wired. "
            "Treat context as neutral; not financial advice."
        )
        print(f"Using PMEX market context...\n  {note}\n")
        return note

    note = (
        "Pakistan Stock Exchange context: no live broad sentiment feed is configured. "
        "Use technicals as the primary signal and treat market-wide context as neutral."
    )
    print(f"Using PSX market context...\n  {note}\n")
    return note


def get_symbols_and_fetcher(
    market: str,
    *,
    symbols_override: Sequence[str] | None = None,
):
    if market == "crypto":
        exchange = get_exchange()
        symbols = (
            list(symbols_override) if symbols_override is not None else configured_crypto_symbols()
        )
        print(f"Using configured crypto universe ({len(symbols)} symbols)...")
        print(f"  {', '.join(symbols)}\n")
        return symbols, lambda symbol: fetch_ohlcv_df(exchange, symbol), exchange.rateLimit / 1000

    if market == "pmex":
        symbols = get_pmex_instruments()
        print(f"Using configured PMEX instruments ({len(symbols)} instruments)...")
        print(f"  {', '.join(symbols)}\n")
        return symbols, fetch_pmex_ohlcv_df, 1

    symbols = configured_psx_symbols()
    print(f"Using configured PSX universe ({len(symbols)} symbols)...")
    print(f"  {', '.join(symbols)}\n")
    return symbols, fetch_psx_ohlcv_df, 1


def scan_market(
    market: str,
    *,
    symbols: Sequence[str] | None = None,
) -> pd.DataFrame:
    print(f"\n=== Scanning {market.upper()} ===")
    sentiment_note = get_market_context(market)
    symbols, fetch_ohlcv, sleep_seconds = get_symbols_and_fetcher(
        market,
        symbols_override=symbols,
    )

    results = []
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i}/{len(symbols)}] Analyzing {symbol}...")
        try:
            df = fetch_ohlcv(symbol)
            if len(df) < 30:
                print("  skipped: not enough candle history")
                continue

            technicals = summarize_technical(df)
            signal = analyze(symbol, technicals, sentiment_note, market_name=market)
            results.append(signal)

            print(f"  -> {signal['signal']} (confidence: {signal['confidence']})")
            time.sleep(sleep_seconds)

        except AIAuthenticationError, AIConfigurationError:
            # Fail closed on auth/config — do not continue with a partial poisoned run.
            raise
        except AIExecutionError as e:
            print(f"  error analyzing {symbol}: {e}")
            continue
        except Exception as e:
            print(f"  error analyzing {symbol}: {e}")
            continue

    return pd.DataFrame(results)


def save_results(
    workbook_results: dict[str, pd.DataFrame],
    selected_market: str,
    *,
    generator: str = PRODUCTION_GENERATOR,
    source: str = "main.py",
    output_dir: str | Path | None = None,
) -> str:
    """Persist market sheets plus ``_Meta`` generator metadata.

    Production scans default to ``outputs/production/`` with
    ``generator=production_scan``. Proof/test callers must pass a non-production
    generator (and optionally ``output_dir`` under ``artifacts/proof/``).
    """
    ensure_artifact_dirs()
    target_dir = Path(output_dir) if output_dir is not None else output_dir_for_generator(generator)
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / (
        f"signals_{selected_market}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        write_meta_sheet(
            writer,
            generator=generator,
            selected_market=selected_market,
            source=source,
        )
        for market, df_results in workbook_results.items():
            sheet_name = MARKET_SHEETS[market]
            if df_results.empty:
                df_results = pd.DataFrame(
                    [
                        {
                            "symbol": "n/a",
                            "signal": "n/a",
                            "confidence": "n/a",
                            "reasoning": "No symbols produced enough data to analyze.",
                            "fomo_fear_note": "n/a",
                            "invalidation": "n/a",
                        }
                    ]
                )
            df_results.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes = "A2"
            for column_cells in worksheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(
                    max(max_length + 2, 12), 70
                )
    return str(out_path.resolve())


def print_summary(workbook_results: dict[str, pd.DataFrame], out_path: str) -> None:
    print("\n=== Summary ===")
    for market, df_results in workbook_results.items():
        print(f"\n{MARKET_SHEETS[market]} sheet:")
        if df_results.empty:
            print("No symbols produced enough data to analyze.")
            continue
        print(df_results[["symbol", "signal", "confidence"]].to_string(index=False))

        buys = df_results[df_results["signal"] == "BUY"]
        if len(buys) > 0:
            print(f"{len(buys)} BUY signal(s) found. Review the reasoning column before acting.")

    print(f"\nFull results saved to Excel workbook: {out_path}")


def run_scan(market: str = MARKET) -> None:
    selected_market = market.lower()
    print(f"=== LLM Signal Bot ({selected_market.upper()}) ===  {datetime.now().isoformat()}")
    print(f"Mode: {'SIGNAL-ONLY (no live orders)' if SIGNAL_ONLY else 'LIVE EXECUTION'}\n")
    print_startup_diagnostics()
    assert_ai_ready(verify_remote=True)
    print("  Authentication: OK\n")

    workbook_results = {}
    for market_name in markets_to_run(selected_market):
        workbook_results[market_name] = scan_market(market_name)

    out_path = save_results(
        workbook_results,
        selected_market,
        generator=PRODUCTION_GENERATOR,
        source="main.py",
    )
    print_summary(workbook_results, out_path)


if __name__ == "__main__":
    args = parse_args()
    run_scan(args.market)
