"""Shared STRATEGY-001 fixtures."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from market_data.models.candle import Candle
from strategy_builder import (
    ComparisonOperator,
    ComparisonRule,
    ConstantOperand,
    EntryRules,
    IndicatorKind,
    IndicatorOperand,
    IndicatorSpec,
    ProtectionKind,
    ProtectionRule,
    StrategyDefinition,
    StrategyDraft,
    create_strategy,
)
from strategy_builder.examples import (
    bollinger_mean_reversion_strategy,
    ema_crossover_rsi_strategy,
    macd_volume_confirmation_strategy,
)


def candles(
    closes: tuple[float, ...],
    *,
    volumes: tuple[float, ...] | None = None,
) -> tuple[Candle, ...]:
    """Build chronological valid OHLCV candles."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    selected_volumes = volumes or tuple(100.0 + index for index in range(len(closes)))
    return tuple(
        Candle(
            record_id=f"candle-{index}",
            dataset_id="dataset-1",
            symbol_id="BTC/USDT",
            timestamp=base + timedelta(hours=index),
            open=close,
            high=close + 1.0,
            low=close - 1.0,
            close=close,
            volume=selected_volumes[index],
            sequence=index,
        )
        for index, close in enumerate(closes)
    )


def crossing_strategy(*, enabled: bool = True) -> StrategyDefinition:
    """Simple close/constant strategy that makes crossing tests explicit."""
    close = IndicatorOperand(indicator_id="close")
    return create_strategy(
        StrategyDraft(
            name="Close Crossing Test",
            version="1.0.0",
            market="crypto:binance",
            supported_timeframes=("1h",),
            entry_rules=EntryRules(
                buy=ComparisonRule(
                    rule_id="buy-cross",
                    operator=ComparisonOperator.CROSSING_ABOVE,
                    left=close,
                    right=ConstantOperand(value=10.0),
                ),
                sell=ComparisonRule(
                    rule_id="sell-cross",
                    operator=ComparisonOperator.CROSSING_BELOW,
                    left=close,
                    right=ConstantOperand(value=10.0),
                ),
            ),
            exit_rules=ComparisonRule(
                rule_id="exit-at-twelve",
                operator=ComparisonOperator.EQUALS,
                left=close,
                right=ConstantOperand(value=12.0),
            ),
            risk_configuration_reference="risk:test@1.0.0",
            stop_loss_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.02),
            take_profit_rule=ProtectionRule(kind=ProtectionKind.PERCENTAGE, value=0.04),
            required_indicators=(IndicatorSpec(indicator_id="close", kind=IndicatorKind.CLOSE),),
            enabled=enabled,
            description="Test-only crossing strategy.",
            tags=("test",),
        )
    )


def example_strategies() -> tuple[StrategyDefinition, ...]:
    """Return all required STRATEGY-001 examples."""
    return (
        ema_crossover_rsi_strategy(),
        bollinger_mean_reversion_strategy(),
        macd_volume_confirmation_strategy(),
    )
