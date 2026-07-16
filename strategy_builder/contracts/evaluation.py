"""Rule-evaluation input and output contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel


class StrategyOutcome(StrEnum):
    """Deterministic strategy outcomes."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    EXIT = "EXIT"


class PositionSide(StrEnum):
    """Open-position direction supplied to exit evaluation."""

    LONG = "long"
    SHORT = "short"


class PositionContext(PlatformModel):
    """Minimal context required to authorize EXIT evaluation."""

    side: PositionSide
    entry_price: float = Field(gt=0.0)


class RuleTrace(PlatformModel):
    """Auditable result for one rule or logical group."""

    rule_id: str = Field(min_length=1)
    matched: bool
    explanation: str = Field(min_length=1)


class StrategyEvaluationResult(PlatformModel):
    """Fail-closed strategy evaluation output."""

    strategy_id: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    outcome: StrategyOutcome
    triggered_rule_ids: tuple[str, ...] = Field(default_factory=tuple)
    explanation: str = Field(min_length=1)
    indicator_values: dict[str, float] = Field(default_factory=dict)
    traces: tuple[RuleTrace, ...] = Field(default_factory=tuple)
    valid: bool = True
