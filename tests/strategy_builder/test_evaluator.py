"""Deterministic rule evaluation acceptance tests."""

from __future__ import annotations

from strategy_builder import (
    ComparisonOperator,
    ComparisonRule,
    ConstantOperand,
    EntryRules,
    GroupOperator,
    IndicatorKind,
    IndicatorOperand,
    IndicatorSpec,
    PositionContext,
    PositionSide,
    ProtectionKind,
    ProtectionRule,
    RuleGroup,
    StrategyDefinition,
    StrategyDraft,
    StrategyEvaluator,
    StrategyOutcome,
    create_strategy,
)
from tests.strategy_builder.fixtures import candles, crossing_strategy


def _logical_strategy() -> StrategyDefinition:
    close = IndicatorOperand(indicator_id="close")
    return create_strategy(
        StrategyDraft(
            name="Logical Group Test",
            version="1.0.0",
            market="crypto:binance",
            supported_timeframes=("1h",),
            entry_rules=EntryRules(
                buy=RuleGroup(
                    rule_id="buy-and",
                    operator=GroupOperator.AND,
                    children=(
                        ComparisonRule(
                            rule_id="above-ten",
                            operator=ComparisonOperator.GREATER_THAN,
                            left=close,
                            right=ConstantOperand(value=10.0),
                        ),
                        ComparisonRule(
                            rule_id="below-twenty",
                            operator=ComparisonOperator.LESS_THAN,
                            left=close,
                            right=ConstantOperand(value=20.0),
                        ),
                    ),
                ),
                sell=RuleGroup(
                    rule_id="sell-or",
                    operator=GroupOperator.OR,
                    children=(
                        ComparisonRule(
                            rule_id="below-five",
                            operator=ComparisonOperator.LESS_THAN,
                            left=close,
                            right=ConstantOperand(value=5.0),
                        ),
                        ComparisonRule(
                            rule_id="above-thirty",
                            operator=ComparisonOperator.GREATER_THAN,
                            left=close,
                            right=ConstantOperand(value=30.0),
                        ),
                    ),
                ),
            ),
            exit_rules=ComparisonRule(
                rule_id="logical-exit",
                operator=ComparisonOperator.EQUALS,
                left=close,
                right=ConstantOperand(value=25.0),
            ),
            risk_configuration_reference="risk:test@1.0.0",
            stop_loss_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.02),
            take_profit_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.04),
            required_indicators=(IndicatorSpec(indicator_id="close", kind=IndicatorKind.CLOSE),),
        )
    )


def _evaluate(
    strategy: StrategyDefinition,
    values: tuple[float, ...],
    *,
    position: bool = False,
):
    return StrategyEvaluator().evaluate(
        strategy,
        candles(values),
        market="crypto:binance",
        timeframe="1h",
        position=(PositionContext(side=PositionSide.LONG, entry_price=10.0) if position else None),
    )


def test_and_and_or_groups_drive_buy_and_sell() -> None:
    strategy = _logical_strategy()
    buy = _evaluate(strategy, (15.0,))
    sell = _evaluate(strategy, (40.0,))
    assert buy.outcome == StrategyOutcome.BUY
    assert {"above-ten", "below-twenty", "buy-and"} <= set(buy.triggered_rule_ids)
    assert sell.outcome == StrategyOutcome.SELL
    assert {"above-thirty", "sell-or"} <= set(sell.triggered_rule_ids)


def test_crossing_above_below_hold_and_exit_outcomes() -> None:
    strategy = crossing_strategy()
    buy = _evaluate(strategy, (9.0, 11.0))
    sell = _evaluate(strategy, (11.0, 9.0))
    hold = _evaluate(strategy, (8.0, 9.0))
    exit_result = _evaluate(strategy, (11.0, 12.0), position=True)
    assert buy.outcome == StrategyOutcome.BUY
    assert buy.triggered_rule_ids == ("buy-cross",)
    assert sell.outcome == StrategyOutcome.SELL
    assert sell.triggered_rule_ids == ("sell-cross",)
    assert hold.outcome == StrategyOutcome.HOLD
    assert exit_result.outcome == StrategyOutcome.EXIT
    assert exit_result.triggered_rule_ids == ("exit-at-twelve",)


def test_insufficient_history_and_disabled_strategy_fail_closed() -> None:
    insufficient = _evaluate(crossing_strategy(), (11.0,))
    disabled = _evaluate(crossing_strategy(enabled=False), (9.0, 11.0))
    assert insufficient.outcome == StrategyOutcome.HOLD
    assert not insufficient.valid
    assert "previous" in insufficient.explanation
    assert disabled.outcome == StrategyOutcome.HOLD
    assert not disabled.valid
    assert "disabled" in disabled.explanation


def test_future_candle_cannot_change_prefix_evaluation() -> None:
    strategy = crossing_strategy()
    available = candles((9.0, 11.0))
    future = candles((9.0, 11.0, 5.0))
    prefix_result = StrategyEvaluator().evaluate(
        strategy,
        available,
        market="crypto:binance",
        timeframe="1h",
    )
    repeated_prefix = StrategyEvaluator().evaluate(
        strategy,
        future[:2],
        market="crypto:binance",
        timeframe="1h",
    )
    full_result = StrategyEvaluator().evaluate(
        strategy,
        future,
        market="crypto:binance",
        timeframe="1h",
    )
    assert prefix_result == repeated_prefix
    assert prefix_result.outcome == StrategyOutcome.BUY
    assert full_result.outcome == StrategyOutcome.SELL


def test_non_chronological_data_fails_closed() -> None:
    strategy = crossing_strategy()
    reversed_candles = tuple(reversed(candles((9.0, 11.0))))
    result = StrategyEvaluator().evaluate(
        strategy,
        reversed_candles,
        market="crypto:binance",
        timeframe="1h",
    )
    assert result.outcome == StrategyOutcome.HOLD
    assert not result.valid
    assert "chronological" in result.explanation
