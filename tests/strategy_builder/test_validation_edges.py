"""Fail-closed validation edges for STRATEGY-001."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from strategy_builder import (
    CandleField,
    ComparisonOperator,
    ComparisonRule,
    ConstantOperand,
    EntryRules,
    IndicatorKind,
    IndicatorOperand,
    IndicatorSpec,
    ProtectionKind,
    ProtectionRule,
    StrategyDraft,
    StrategyEvaluator,
    StrategyNotFoundError,
    StrategyOutcome,
    StrategyRegistry,
    StrategyValidationError,
    create_strategy,
    deserialize_strategy,
)
from strategy_builder.exceptions import IndicatorEvaluationError
from strategy_builder.indicators import evaluate_indicator
from tests.strategy_builder.fixtures import candles, crossing_strategy


def _content() -> dict[str, object]:
    strategy = crossing_strategy()
    return {name: getattr(strategy, name) for name in StrategyDraft.model_fields}


@pytest.mark.parametrize(
    "payload, message",
    [
        (
            {"indicator_id": "close", "kind": IndicatorKind.CLOSE, "period": 2},
            "do not accept periods",
        ),
        (
            {"indicator_id": "sma", "kind": IndicatorKind.SMA},
            "requires period",
        ),
        (
            {
                "indicator_id": "macd",
                "kind": IndicatorKind.MACD,
                "fast_period": 5,
                "slow_period": 3,
                "signal_period": 2,
            },
            "fast_period must be less",
        ),
        (
            {
                "indicator_id": "band",
                "kind": IndicatorKind.BOLLINGER_UPPER,
                "period": 5,
            },
            "require standard_deviations",
        ),
        (
            {
                "indicator_id": "atr",
                "kind": IndicatorKind.ATR,
                "period": 5,
                "source": CandleField.HIGH,
            },
            "requires source=close",
        ),
    ],
)
def test_invalid_indicator_parameter_combinations(
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        IndicatorSpec.model_validate(payload)


def test_invalid_rule_and_protection_shapes_are_rejected() -> None:
    with pytest.raises(ValidationError, match="finite"):
        ConstantOperand(value=float("inf"))
    with pytest.raises(ValidationError, match="does not accept range"):
        ComparisonRule(
            rule_id="bad",
            operator=ComparisonOperator.GREATER_THAN,
            left=ConstantOperand(value=2.0),
            right=ConstantOperand(value=1.0),
            lower=ConstantOperand(value=0.0),
        )
    with pytest.raises(ValidationError, match="only valid for equals"):
        ComparisonRule(
            rule_id="bad-tolerance",
            operator=ComparisonOperator.LESS_THAN,
            left=ConstantOperand(value=1.0),
            right=ConstantOperand(value=2.0),
            equality_tolerance=0.1,
        )
    with pytest.raises(ValidationError, match="requires indicator_id"):
        ProtectionRule(kind=ProtectionKind.ATR_MULTIPLE, value=2.0)
    with pytest.raises(ValidationError, match="does not accept indicator"):
        ProtectionRule(
            kind=ProtectionKind.PERCENTAGE,
            value=0.1,
            indicator_id="atr",
        )


def test_strategy_collection_invariants_are_rejected() -> None:
    duplicate_timeframes = _content()
    duplicate_timeframes["supported_timeframes"] = ("1h", "1h")
    with pytest.raises(ValidationError, match="timeframes must be unique"):
        StrategyDraft.model_validate(duplicate_timeframes)

    duplicate_tags = _content()
    duplicate_tags["tags"] = ("same", "same")
    with pytest.raises(ValidationError, match="tags must be unique"):
        StrategyDraft.model_validate(duplicate_tags)

    duplicate_indicators = _content()
    indicator = IndicatorSpec(indicator_id="close", kind=IndicatorKind.CLOSE)
    duplicate_indicators["required_indicators"] = (indicator, indicator)
    with pytest.raises(ValidationError, match="indicator IDs must be unique"):
        StrategyDraft.model_validate(duplicate_indicators)

    duplicate_rules = _content()
    close = IndicatorOperand(indicator_id="close")
    duplicate_rules["entry_rules"] = EntryRules(
        buy=ComparisonRule(
            rule_id="same-rule",
            operator=ComparisonOperator.GREATER_THAN,
            left=close,
            right=ConstantOperand(value=1.0),
        ),
        sell=ComparisonRule(
            rule_id="same-rule",
            operator=ComparisonOperator.LESS_THAN,
            left=close,
            right=ConstantOperand(value=1.0),
        ),
    )
    with pytest.raises(ValidationError, match="rule IDs must be unique"):
        StrategyDraft.model_validate(duplicate_rules)


def test_evaluator_rejects_context_mismatch_and_conflicts() -> None:
    strategy = crossing_strategy()
    history = candles((9.0, 11.0))
    wrong_market = StrategyEvaluator().evaluate(
        strategy,
        history,
        market="psx",
        timeframe="1h",
    )
    wrong_timeframe = StrategyEvaluator().evaluate(
        strategy,
        history,
        market="crypto:binance",
        timeframe="5m",
    )
    assert not wrong_market.valid
    assert not wrong_timeframe.valid

    content = _content()
    close = IndicatorOperand(indicator_id="close")
    content["entry_rules"] = EntryRules(
        buy=ComparisonRule(
            rule_id="conflict-buy",
            operator=ComparisonOperator.GREATER_THAN,
            left=close,
            right=ConstantOperand(value=1.0),
        ),
        sell=ComparisonRule(
            rule_id="conflict-sell",
            operator=ComparisonOperator.GREATER_THAN,
            left=close,
            right=ConstantOperand(value=1.0),
        ),
    )
    conflict = StrategyEvaluator().evaluate(
        create_strategy(StrategyDraft.model_validate(content)),
        candles((10.0,)),
        market="crypto:binance",
        timeframe="1h",
    )
    assert conflict.outcome == StrategyOutcome.HOLD
    assert not conflict.valid
    assert "Conflicting" in conflict.explanation


def test_invalid_serialization_registry_and_indicator_inputs() -> None:
    with pytest.raises(StrategyValidationError, match="Invalid strategy JSON"):
        deserialize_strategy("{not-json")
    with pytest.raises(StrategyNotFoundError):
        StrategyRegistry().resolve("strategy-0000000000000000", "1.0.0")
    with pytest.raises(IndicatorEvaluationError, match="at least one"):
        evaluate_indicator(
            IndicatorSpec(
                indicator_id="volume",
                kind=IndicatorKind.VOLUME,
                source=CandleField.VOLUME,
            ),
            (),
        )
