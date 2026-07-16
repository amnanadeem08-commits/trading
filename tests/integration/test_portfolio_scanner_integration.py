"""PORTFOLIO-001 integration with the existing crypto scanner."""

from __future__ import annotations

import pandas as pd

import main
from portfolio_sync import stable_unique_symbols


def test_portfolio_symbols_are_scanned_once_without_changing_signal_logic(
    monkeypatch,
) -> None:
    final_symbols = stable_unique_symbols(
        ("XRP/USDT",),
        ("BTC/USDT", "ETH/USDT", "BNB/USDT", "BTC/USDT"),
    )
    captured: list[str] = []
    history = pd.DataFrame(
        {
            "open": [100.0] * 30,
            "high": [101.0] * 30,
            "low": [99.0] * 30,
            "close": [100.0] * 30,
            "volume": [1_000.0] * 30,
        }
    )

    def fake_get_symbols(market: str, *, symbols_override=None):
        assert market == "crypto"
        symbols = list(symbols_override)

        def fetch(symbol: str) -> pd.DataFrame:
            captured.append(symbol)
            return history

        return symbols, fetch, 0.0

    monkeypatch.setattr(main, "get_symbols_and_fetcher", fake_get_symbols)
    monkeypatch.setattr(main, "get_market_context", lambda _market: "neutral")
    monkeypatch.setattr(
        main,
        "analyze",
        lambda symbol, *_args, **_kwargs: {
            "symbol": symbol,
            "signal": "HOLD",
            "confidence": "medium",
            "reasoning": "Existing signal logic result.",
        },
    )
    monkeypatch.setattr(main.time, "sleep", lambda _seconds: None)

    result = main.scan_market("crypto", symbols=final_symbols)
    assert captured == ["XRP/USDT", "BTC/USDT", "ETH/USDT", "BNB/USDT"]
    assert set(result["symbol"]) >= {"BTC/USDT", "ETH/USDT", "BNB/USDT"}
