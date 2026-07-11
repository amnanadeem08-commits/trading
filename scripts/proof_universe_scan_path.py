"""Execution-path proof: config → scan → proof workbook (never production)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.signal_universe import (  # noqa: E402
    clear_universe_cache,
    configured_crypto_symbols,
    configured_pmex_instruments,
    configured_psx_symbols,
)
from core.signal_workbook import (  # noqa: E402
    PROOF_DIR,
    ensure_artifact_dirs,
    latest_production_workbook,
    read_workbook_metadata,
)
from dashboard import latest_workbook, load_workbook  # noqa: E402
from main import get_symbols_and_fetcher, save_results, scan_market  # noqa: E402


def _print_stage(title: str, count: int, symbols: list[str]) -> None:
    print(title)
    print(f"  count={count}")
    print(f"  symbols={symbols}")


def main() -> int:
    clear_universe_cache()
    ensure_artifact_dirs()

    print("=== EXECUTION LOG ===")
    print("Symbols loaded from signal_universe.yaml")
    crypto_cfg = configured_crypto_symbols()
    psx_cfg = configured_psx_symbols()
    pmex_cfg = configured_pmex_instruments()
    _print_stage("Configured Crypto", len(crypto_cfg), crypto_cfg)
    _print_stage("Configured PSX", len(psx_cfg), psx_cfg)
    _print_stage("Configured PMEX", len(pmex_cfg), pmex_cfg)

    print("\nTotal count before scan (fetcher lists)")
    crypto_pre, _, _ = get_symbols_and_fetcher("crypto")
    psx_pre, _, _ = get_symbols_and_fetcher("psx")
    pmex_pre, _, _ = get_symbols_and_fetcher("pmex")
    _print_stage("Pre-scan Crypto", len(crypto_pre), crypto_pre)
    _print_stage("Pre-scan PSX", len(psx_pre), psx_pre)
    _print_stage("Pre-scan PMEX", len(pmex_pre), pmex_pre)
    print(f"Total count before scan={len(crypto_pre) + len(psx_pre) + len(pmex_pre)}")

    # Fail closed if any pre-scan truncation exists.
    assert len(crypto_pre) == 20 and len(psx_pre) == 20 and len(pmex_pre) == 7

    import main as main_mod

    def _fake_analyze(symbol: str, technicals: dict, sentiment_note: str, market_name: str = "crypto"):
        return {
            "symbol": symbol,
            "signal": "HOLD",
            "confidence": "low",
            "reasoning": f"Proof scan for {symbol}",
            "fomo_fear_note": "n/a",
            "invalidation": "n/a",
            "provider": "proof",
            "model": "proof",
        }

    def _enough_ohlcv(symbol: str) -> pd.DataFrame:
        # Minimal synthetic candles so scan does not skip for history.
        n = 40
        return pd.DataFrame(
            {
                "timestamp": pd.date_range("2025-01-01", periods=n, freq="D"),
                "open": [100.0] * n,
                "high": [101.0] * n,
                "low": [99.0] * n,
                "close": [100.0 + (i % 3) for i in range(n)],
                "volume": [1000.0] * n,
            }
        )

    main_mod.analyze = _fake_analyze  # type: ignore[method-assign]
    main_mod.summarize_technical = lambda df: {  # type: ignore[method-assign]
        "last_close": float(df["close"].iloc[-1]),
        "rsi": 50.0,
        "rsi_trend": "flat",
        "macd": 0.0,
        "macd_signal": 0.0,
        "macd_histogram": 0.0,
        "macd_crossover": False,
        "volatility_pct": 1.0,
        "price_change_24_candles_pct": 0.0,
        "recent_candles": "proof",
    }
    main_mod.fetch_ohlcv_df = lambda exchange, symbol: _enough_ohlcv(symbol)  # type: ignore[method-assign]
    main_mod.fetch_psx_ohlcv_df = _enough_ohlcv  # type: ignore[method-assign]
    main_mod.fetch_pmex_ohlcv_df = _enough_ohlcv  # type: ignore[method-assign]
    main_mod.get_exchange = lambda: type("E", (), {"rateLimit": 0})()  # type: ignore[method-assign]
    main_mod.time.sleep = lambda _s: None  # type: ignore[method-assign]

    print("\nTotal count after scan")
    crypto_df = scan_market("crypto")
    psx_df = scan_market("psx")
    pmex_df = scan_market("pmex")
    _print_stage(
        "Scanned Crypto",
        len(crypto_df),
        crypto_df["symbol"].astype(str).tolist() if not crypto_df.empty else [],
    )
    _print_stage(
        "Scanned PSX",
        len(psx_df),
        psx_df["symbol"].astype(str).tolist() if not psx_df.empty else [],
    )
    _print_stage(
        "Scanned PMEX",
        len(pmex_df),
        pmex_df["symbol"].astype(str).tolist() if not pmex_df.empty else [],
    )
    print(
        "Total count after scan="
        f"{len(crypto_df) + len(psx_df) + len(pmex_df)}"
    )

    print("\nTotal rows written to workbook")
    out = save_results(
        {"crypto": crypto_df, "psx": psx_df, "pmex": pmex_df},
        "all",
        generator="proof_scan",
        source="scripts/proof_universe_scan_path.py",
        output_dir=PROOF_DIR,
    )
    out_path = Path(out)
    assert out_path.resolve().parent == PROOF_DIR.resolve(), out_path
    meta = read_workbook_metadata(out_path)
    assert meta.get("generator") == "proof_scan", meta

    written = pd.read_excel(out, sheet_name=None)
    market_sheets = {k: v for k, v in written.items() if k != "_Meta"}
    for sheet, df in market_sheets.items():
        print(f"  sheet={sheet} rows={len(df)} symbols={df['symbol'].astype(str).tolist()}")
    print(
        "Total rows written to workbook="
        f"{sum(len(df) for df in market_sheets.values())}"
    )

    print("\nDashboard isolation check")
    latest = latest_workbook()
    prod_latest = latest_production_workbook()
    assert latest is None or latest.resolve() != out_path.resolve(), (
        f"proof workbook must not be selected by latest_workbook(): {latest}"
    )
    assert prod_latest is None or prod_latest.resolve() != out_path.resolve()
    print(f"  proof_workbook={out_path}")
    print(f"  latest_workbook={latest}")
    print(f"  proof_not_loaded_by_dashboard=True")

    # Proof path still loadable by explicit path for count assertions.
    loaded = load_workbook(out_path)
    print("\nTotal rows loaded from proof path (explicit)")
    for market, df in loaded.items():
        print(
            f"  market={market} rows={len(df)} "
            f"symbols={df['symbol'].astype(str).tolist()}"
        )
    print(f"Total rows loaded from proof path={sum(len(df) for df in loaded.values())}")

    assert len(crypto_df) == 20
    assert len(psx_df) == 20
    assert len(pmex_df) == 7
    assert len(written["Crypto"]) == 20
    assert len(written["PSX"]) == 20
    assert len(written["PMEX"]) == 7
    assert len(loaded["crypto"]) == 20
    assert len(loaded["psx"]) == 20
    assert len(loaded["pmex"]) == 7

    print("\nPROOF_OK")
    print(f"workbook={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
