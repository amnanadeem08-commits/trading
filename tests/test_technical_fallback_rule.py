"""Unit tests for technical-rule fallback used when LLM is rate-limited."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SEED = ROOT / "scripts" / "seed_production_workbook_technical.py"
_spec = importlib.util.spec_from_file_location("seed_prod_tech", _SEED)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_signal_from_technicals = _mod._signal_from_technicals


def _tech(**overrides):
    base = {
        "rsi": 50.0,
        "macd_histogram": 0.0,
        "macd_crossover": "none",
        "last_close": 100.0,
        "volatility_pct": 1.0,
    }
    base.update(overrides)
    return base


def test_hard_rsi_buy_without_macd_and() -> None:
    row = _signal_from_technicals("X", _tech(rsi=34.0, macd_histogram=-1.0))
    assert row["signal"] == "BUY"
    assert row["signal_source"] == "technical_rules"
    assert row["llm_used"] is False
    assert row["llm_status"] == "rate_limited"


def test_hard_rsi_sell_without_macd_and() -> None:
    row = _signal_from_technicals("X", _tech(rsi=66.0, macd_histogram=1.0))
    assert row["signal"] == "SELL"


def test_soft_buy_rsi_with_positive_hist() -> None:
    row = _signal_from_technicals("X", _tech(rsi=42.0, macd_histogram=0.5))
    assert row["signal"] == "BUY"


def test_soft_sell_rsi_with_negative_hist() -> None:
    row = _signal_from_technicals("X", _tech(rsi=58.0, macd_histogram=-0.5))
    assert row["signal"] == "SELL"


def test_mid_band_hold() -> None:
    row = _signal_from_technicals("X", _tech(rsi=50.0, macd_histogram=0.1))
    assert row["signal"] == "HOLD"


def test_bullish_crossover_buy() -> None:
    row = _signal_from_technicals("X", _tech(rsi=50.0, macd_crossover="bullish"))
    assert row["signal"] == "BUY"
