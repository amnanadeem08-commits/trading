"""Auditable example strategy definitions for STRATEGY-001."""

from __future__ import annotations

from strategy_builder.contracts import (
    CandleField,
    ComparisonOperator,
    ComparisonRule,
    ConstantOperand,
    EntryRules,
    GroupOperator,
    IndicatorKind,
    IndicatorOperand,
    IndicatorSpec,
    ProtectionKind,
    ProtectionRule,
    RuleGroup,
    StrategyDefinition,
    StrategyDraft,
)
from strategy_builder.identity import create_strategy


def _indicator(indicator_id: str) -> IndicatorOperand:
    return IndicatorOperand(indicator_id=indicator_id)


def _constant(value: float) -> ConstantOperand:
    return ConstantOperand(value=value)


def ema_crossover_rsi_strategy() -> StrategyDefinition:
    """EMA crossover confirmed by a bounded RSI condition."""
    buy = RuleGroup(
        rule_id="ema-rsi-buy",
        operator=GroupOperator.AND,
        children=(
            ComparisonRule(
                rule_id="ema-cross-above",
                operator=ComparisonOperator.CROSSING_ABOVE,
                left=_indicator("ema_fast"),
                right=_indicator("ema_slow"),
            ),
            ComparisonRule(
                rule_id="rsi-buy-confirm",
                operator=ComparisonOperator.LESS_THAN,
                left=_indicator("rsi"),
                right=_constant(70.0),
            ),
        ),
    )
    sell = RuleGroup(
        rule_id="ema-rsi-sell",
        operator=GroupOperator.AND,
        children=(
            ComparisonRule(
                rule_id="ema-cross-below",
                operator=ComparisonOperator.CROSSING_BELOW,
                left=_indicator("ema_fast"),
                right=_indicator("ema_slow"),
            ),
            ComparisonRule(
                rule_id="rsi-sell-confirm",
                operator=ComparisonOperator.GREATER_THAN,
                left=_indicator("rsi"),
                right=_constant(30.0),
            ),
        ),
    )
    exit_rules = RuleGroup(
        rule_id="ema-rsi-exit",
        operator=GroupOperator.OR,
        children=(
            ComparisonRule(
                rule_id="rsi-overbought-exit",
                operator=ComparisonOperator.GREATER_THAN,
                left=_indicator("rsi"),
                right=_constant(80.0),
            ),
            ComparisonRule(
                rule_id="rsi-oversold-exit",
                operator=ComparisonOperator.LESS_THAN,
                left=_indicator("rsi"),
                right=_constant(20.0),
            ),
        ),
    )
    return create_strategy(
        StrategyDraft(
            name="EMA Crossover with RSI Confirmation",
            version="1.0.0",
            market="crypto:binance",
            supported_timeframes=("1h",),
            entry_rules=EntryRules(buy=buy, sell=sell),
            exit_rules=exit_rules,
            risk_configuration_reference="risk:default-spot@1.0.0",
            stop_loss_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.02),
            take_profit_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.04),
            required_indicators=(
                IndicatorSpec(indicator_id="ema_fast", kind=IndicatorKind.EMA, period=3),
                IndicatorSpec(indicator_id="ema_slow", kind=IndicatorKind.EMA, period=5),
                IndicatorSpec(indicator_id="rsi", kind=IndicatorKind.RSI, period=3),
            ),
            description="EMA crossover confirmed by RSI; deterministic research example.",
            tags=("example", "ema", "rsi"),
        )
    )


def bollinger_mean_reversion_strategy() -> StrategyDefinition:
    """Bollinger-band mean-reversion example."""
    return create_strategy(
        StrategyDraft(
            name="Bollinger Mean Reversion",
            version="1.0.0",
            market="crypto:binance",
            supported_timeframes=("1h",),
            entry_rules=EntryRules(
                buy=ComparisonRule(
                    rule_id="bollinger-buy",
                    operator=ComparisonOperator.LESS_THAN,
                    left=_indicator("close"),
                    right=_indicator("bb_lower"),
                ),
                sell=ComparisonRule(
                    rule_id="bollinger-sell",
                    operator=ComparisonOperator.GREATER_THAN,
                    left=_indicator("close"),
                    right=_indicator("bb_upper"),
                ),
            ),
            exit_rules=ComparisonRule(
                rule_id="bollinger-middle-exit",
                operator=ComparisonOperator.EQUALS,
                left=_indicator("close"),
                right=_indicator("bb_middle"),
                equality_tolerance=0.5,
            ),
            risk_configuration_reference="risk:default-spot@1.0.0",
            stop_loss_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.02),
            take_profit_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.03),
            required_indicators=(
                IndicatorSpec(indicator_id="close", kind=IndicatorKind.CLOSE),
                IndicatorSpec(
                    indicator_id="bb_lower",
                    kind=IndicatorKind.BOLLINGER_LOWER,
                    period=5,
                    standard_deviations=2.0,
                ),
                IndicatorSpec(
                    indicator_id="bb_middle",
                    kind=IndicatorKind.BOLLINGER_MIDDLE,
                    period=5,
                    standard_deviations=2.0,
                ),
                IndicatorSpec(
                    indicator_id="bb_upper",
                    kind=IndicatorKind.BOLLINGER_UPPER,
                    period=5,
                    standard_deviations=2.0,
                ),
            ),
            description="Band-extreme entries with a middle-band exit.",
            tags=("example", "bollinger", "mean-reversion"),
        )
    )


def macd_volume_confirmation_strategy() -> StrategyDefinition:
    """MACD crossover requiring volume above its moving average."""
    volume_confirmation = ComparisonRule(
        rule_id="volume-confirm-buy",
        operator=ComparisonOperator.GREATER_THAN,
        left=_indicator("volume"),
        right=_indicator("volume_average"),
    )
    return create_strategy(
        StrategyDraft(
            name="MACD with Volume Confirmation",
            version="1.0.0",
            market="crypto:binance",
            supported_timeframes=("1h",),
            entry_rules=EntryRules(
                buy=RuleGroup(
                    rule_id="macd-volume-buy",
                    operator=GroupOperator.AND,
                    children=(
                        ComparisonRule(
                            rule_id="macd-cross-above",
                            operator=ComparisonOperator.CROSSING_ABOVE,
                            left=_indicator("macd"),
                            right=_indicator("macd_signal"),
                        ),
                        volume_confirmation,
                    ),
                ),
                sell=RuleGroup(
                    rule_id="macd-volume-sell",
                    operator=GroupOperator.AND,
                    children=(
                        ComparisonRule(
                            rule_id="macd-cross-below",
                            operator=ComparisonOperator.CROSSING_BELOW,
                            left=_indicator("macd"),
                            right=_indicator("macd_signal"),
                        ),
                        ComparisonRule(
                            rule_id="volume-confirm-sell",
                            operator=ComparisonOperator.GREATER_THAN,
                            left=_indicator("volume"),
                            right=_indicator("volume_average"),
                        ),
                    ),
                ),
            ),
            exit_rules=ComparisonRule(
                rule_id="macd-convergence-exit",
                operator=ComparisonOperator.EQUALS,
                left=_indicator("macd"),
                right=_indicator("macd_signal"),
                equality_tolerance=0.01,
            ),
            risk_configuration_reference="risk:default-spot@1.0.0",
            stop_loss_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.02),
            take_profit_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.04),
            required_indicators=(
                IndicatorSpec(
                    indicator_id="volume",
                    kind=IndicatorKind.VOLUME,
                    source=CandleField.VOLUME,
                ),
                IndicatorSpec(
                    indicator_id="volume_average",
                    kind=IndicatorKind.VOLUME_MOVING_AVERAGE,
                    source=CandleField.VOLUME,
                    period=3,
                ),
                IndicatorSpec(
                    indicator_id="macd",
                    kind=IndicatorKind.MACD,
                    fast_period=3,
                    slow_period=5,
                    signal_period=2,
                ),
                IndicatorSpec(
                    indicator_id="macd_signal",
                    kind=IndicatorKind.MACD_SIGNAL,
                    fast_period=3,
                    slow_period=5,
                    signal_period=2,
                ),
            ),
            description="MACD crossover accepted only with above-average volume.",
            tags=("example", "macd", "volume"),
        )
    )
