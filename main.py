"""
Run this to scan Binance/USDT crypto pairs, Pakistan Stock Exchange symbols,
or both markets in one Excel workbook.

SIGNAL-ONLY MODE: this prints/saves recommendations. It does NOT place
trades. That's deliberate - read the README before wiring up execution.

Usage:
    python main.py
    python main.py --market both
    python main.py --market psx
    python main.py --market crypto
"""

import argparse
import time
import pandas as pd
from datetime import datetime

from config import MARKET, TOP_N, SIGNAL_ONLY
from connectors.binance_connector import get_exchange, get_top_n_symbols, fetch_ohlcv_df
from connectors.psx_connector import get_psx_symbols, fetch_psx_ohlcv_df
from core.indicators import summarize_technical
from core.sentiment import fetch_fear_greed, interpret_for_prompt
from core.llm_analyzer import AIAuthenticationError, AIConfigurationError, AIExecutionError, analyze, assert_ai_ready, print_startup_diagnostics


MARKET_SHEETS = {
    "psx": "PSX",
    "crypto": "Crypto",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Scan crypto, PSX, or both for LLM trade signals.")
    parser.add_argument(
        "--market",
        choices=["crypto", "psx", "both"],
        default=MARKET,
        help="Market to scan: crypto, psx, or both for a multi-sheet Excel workbook.",
    )
    return parser.parse_args()


def markets_to_run(market: str) -> list[str]:
    market = market.lower()
    if market == "both":
        return ["psx", "crypto"]
    return [market]


def get_market_context(market: str) -> str:
    if market == "crypto":
        print("Fetching market-wide crypto sentiment...")
        fg = fetch_fear_greed()
        sentiment_note = interpret_for_prompt(fg)
        print(f"  {sentiment_note}\n")
        return sentiment_note

    note = (
        "Pakistan Stock Exchange context: no live broad sentiment feed is configured. "
        "Use technicals as the primary signal and treat market-wide context as neutral."
    )
    print(f"Using PSX market context...\n  {note}\n")
    return note


def get_symbols_and_fetcher(market: str):
    if market == "crypto":
        exchange = get_exchange()
        print(f"Fetching top {TOP_N} Binance/USDT symbols by volume...")
        symbols = get_top_n_symbols(exchange, n=TOP_N)
        print(f"  {', '.join(symbols)}\n")
        return symbols, lambda symbol: fetch_ohlcv_df(exchange, symbol), exchange.rateLimit / 1000

    print(f"Fetching configured top {TOP_N} PSX symbols...")
    symbols = get_psx_symbols(n=TOP_N)
    print(f"  {', '.join(symbols)}\n")
    return symbols, fetch_psx_ohlcv_df, 1


def scan_market(market: str) -> pd.DataFrame:
    print(f"\n=== Scanning {market.upper()} ===")
    sentiment_note = get_market_context(market)
    symbols, fetch_ohlcv, sleep_seconds = get_symbols_and_fetcher(market)

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

        except (AIAuthenticationError, AIConfigurationError, AIExecutionError):
            raise
        except Exception as e:
            print(f"  error analyzing {symbol}: {e}")
            continue

    return pd.DataFrame(results)


def save_results(workbook_results: dict[str, pd.DataFrame], selected_market: str) -> str:
    out_path = f"signals_{selected_market}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for market, df_results in workbook_results.items():
            sheet_name = MARKET_SHEETS[market]
            if df_results.empty:
                df_results = pd.DataFrame([{
                    "symbol": "n/a",
                    "signal": "n/a",
                    "confidence": "n/a",
                    "reasoning": "No symbols produced enough data to analyze.",
                    "fomo_fear_note": "n/a",
                    "invalidation": "n/a",
                }])
            df_results.to_excel(writer, sheet_name=sheet_name, index=False)

            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes = "A2"
            for column_cells in worksheet.columns:
                max_length = max(len(str(cell.value or "")) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, 12), 70)
    return out_path


def print_summary(workbook_results: dict[str, pd.DataFrame], out_path: str):
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


def run_scan(market: str = MARKET):
    selected_market = market.lower()
    print(f"=== LLM Signal Bot ({selected_market.upper()}) ===  {datetime.now().isoformat()}")
    print(f"Mode: {'SIGNAL-ONLY (no live orders)' if SIGNAL_ONLY else 'LIVE EXECUTION'}\n")
    print_startup_diagnostics()
    assert_ai_ready(verify_remote=True)
    print("  Authentication: OK\n")

    workbook_results = {}
    for market_name in markets_to_run(selected_market):
        workbook_results[market_name] = scan_market(market_name)

    out_path = save_results(workbook_results, selected_market)
    print_summary(workbook_results, out_path)


if __name__ == "__main__":
    args = parse_args()
    run_scan(args.market)

