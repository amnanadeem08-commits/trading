"""STRATEGY-001 compatibility with the accepted Backtesting V1 signal boundary."""

from __future__ import annotations

from models.decision import DecisionState
from models.signal import ExplainableSignal
from strategy_builder import PositionContext, PositionSide
from strategy_builder.adapters import (
    evaluate_strategy_candidate_at_bar,
    evaluate_strategy_signal_at_bar,
)
from tests.strategy_builder.fixtures import candles, crossing_strategy


def test_adapter_returns_existing_direction_candidate_contract() -> None:
    strategy = crossing_strategy()
    candidate = evaluate_strategy_candidate_at_bar(
        candles((9.0, 11.0)),
        strategy=strategy,
        market_id="crypto:binance",
        timeframe="1h",
    )
    assert candidate is not None
    assert candidate.decision == DecisionState.BUY
    assert candidate.indicator_values["triggered_rule_ids"] == "buy-cross"


def test_adapter_builds_backtesting_explainable_signal_without_engine_changes() -> None:
    strategy = crossing_strategy()
    signal = evaluate_strategy_signal_at_bar(
        candles((9.0, 11.0)),
        strategy=strategy,
        market_id="crypto:binance",
        timeframe="1h",
        bar_index=1,
        config_hash="strategy-test",
    )
    assert isinstance(signal, ExplainableSignal)
    assert signal.decision == DecisionState.BUY
    assert signal.provenance.strategy_version == strategy.version
    assert signal.reproducibility.config_hash == "strategy-test"


def test_exit_maps_to_full_exit_and_future_bars_are_not_required() -> None:
    strategy = crossing_strategy()
    available = candles((11.0, 12.0))
    candidate = evaluate_strategy_candidate_at_bar(
        available,
        strategy=strategy,
        market_id="crypto:binance",
        timeframe="1h",
        position=PositionContext(side=PositionSide.LONG, entry_price=11.0),
    )
    assert candidate is not None
    assert candidate.decision == DecisionState.FULL_EXIT

    repeated = evaluate_strategy_candidate_at_bar(
        candles((11.0, 12.0, 1.0))[:2],
        strategy=strategy,
        market_id="crypto:binance",
        timeframe="1h",
        position=PositionContext(side=PositionSide.LONG, entry_price=11.0),
    )
    assert repeated == candidate
