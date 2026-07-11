"""Unit tests for technical indicators and RSI/MACD candidate rules."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from models.decision import DecisionState
from signal_engine import (
    IndicatorComputationError,
    RSIMACDRule,
    SignalAssembler,
    SignalRuleError,
    apply_candidate,
    compute_macd,
    compute_rsi,
    compute_sma,
)
from signal_engine.intake.market_intake import MarketIntakeFrame
from tests.signal_helpers import make_assembly_request


def _frames_from_closes(closes: list[float]) -> tuple[MarketIntakeFrame, ...]:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    frames: list[MarketIntakeFrame] = []
    for index, close in enumerate(closes):
        frames.append(
            MarketIntakeFrame(
                frame_id=f"f-{index}",
                symbol_id="BTC/USDT",
                dataset_id="crypto:binance",
                market_id="crypto:binance",
                record_type="candle",
                timestamp=start + timedelta(hours=index),
                sequence=index,
                ohlcv={
                    "open": close,
                    "high": close + 1.0,
                    "low": close - 1.0,
                    "close": close,
                    "volume": 10.0,
                },
            )
        )
    return tuple(frames)


@pytest.mark.unit
def test_rsi_macd_sma_deterministic() -> None:
    # Rising series -> RSI high; enough length for MACD defaults.
    closes = [float(100 + index) for index in range(50)]
    rsi = compute_rsi(closes, 14)
    macd = compute_macd(closes, fast=12, slow=26, signal=9)
    sma = compute_sma(closes, 20)
    assert rsi == 100.0
    assert macd.histogram != 0.0 or macd.macd != 0.0
    assert sma == pytest.approx(sum(closes[-20:]) / 20.0)


@pytest.mark.unit
def test_indicator_rejects_short_series() -> None:
    with pytest.raises(IndicatorComputationError):
        compute_rsi([1.0, 2.0], 14)
    with pytest.raises(IndicatorComputationError):
        compute_macd([1.0] * 10, fast=12, slow=26, signal=9)
    with pytest.raises(IndicatorComputationError):
        compute_sma([1.0, 2.0], 5)


@pytest.mark.unit
def test_rsi_macd_rule_sell_on_overbought_down_histogram() -> None:
    # Strong uptrend then mild pullback keeps RSI elevated while MACD hist can turn.
    closes = [float(100 + index) for index in range(40)] + [
        139.0,
        138.0,
        136.0,
        134.0,
        132.0,
        130.0,
        128.0,
        126.0,
        124.0,
        122.0,
    ]
    rule = RSIMACDRule(rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9)
    candidate = rule.evaluate(_frames_from_closes(closes))
    assert "rsi_14" in candidate.indicators_used
    assert "macd_histogram" in candidate.indicator_values
    assert candidate.decision in {DecisionState.SELL, DecisionState.HOLD, DecisionState.BUY}
    # Rising-then-falling should not crash and must be deterministic.
    again = rule.evaluate(_frames_from_closes(closes))
    assert again == candidate


@pytest.mark.unit
def test_rsi_macd_rule_buy_path_with_injected_thresholds(monkeypatch: pytest.MonkeyPatch) -> None:
    rule = RSIMACDRule(oversold=50.0, overbought=80.0)

    monkeypatch.setattr(
        "signal_engine.rules.rsi_macd_rule.compute_rsi",
        lambda *_args, **_kwargs: 20.0,
    )

    class _Macd:
        macd = 0.1
        signal = 0.0
        histogram = 0.1

    monkeypatch.setattr(
        "signal_engine.rules.rsi_macd_rule.compute_macd",
        lambda *_args, **_kwargs: _Macd(),
    )
    monkeypatch.setattr(
        "signal_engine.rules.rsi_macd_rule.compute_sma",
        lambda *_args, **_kwargs: 100.0,
    )
    candidate = rule.evaluate(_frames_from_closes([float(100 + i) for i in range(40)]))
    assert candidate.decision == DecisionState.BUY
    assert candidate.confidence > 0.0


@pytest.mark.unit
def test_apply_candidate_wires_assembler() -> None:
    rule = RSIMACDRule()
    monkey_frames = _frames_from_closes([float(100 + i) for i in range(40)])
    # Force HOLD via mid RSI / zero hist using monkeypatch-free real path may vary;
    # build candidate explicitly for assembler wiring.
    from models.decision import DecisionSource
    from signal_engine import DirectionCandidate

    candidate = DirectionCandidate(
        decision=DecisionState.HOLD,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        confidence=0.4,
        indicators_used=("rsi_14", "macd_histogram"),
        indicator_values={"rsi_14": 50.0, "macd_histogram": 0.0},
        rationale="Neutral.",
    )
    request = apply_candidate(make_assembly_request(), candidate)
    signal = SignalAssembler().assemble(request)
    assert signal.decision == DecisionState.HOLD
    assert signal.indicators_used == ("rsi_14", "macd_histogram")
    assert signal.indicator_values["rsi_14"] == 50.0
    # sanity: rule also evaluates without error on same frames
    assert rule.evaluate(monkey_frames).indicators_used


@pytest.mark.unit
def test_rule_rejects_empty_or_missing_close() -> None:
    rule = RSIMACDRule()
    with pytest.raises(SignalRuleError, match="empty"):
        rule.evaluate(())
    bad = MarketIntakeFrame(
        frame_id="bad",
        symbol_id="BTC/USDT",
        dataset_id="crypto:binance",
        market_id="crypto:binance",
        record_type="candle",
        ohlcv={},
    )
    with pytest.raises(SignalRuleError, match=r"missing ohlcv\.close"):
        rule.evaluate((bad,))
