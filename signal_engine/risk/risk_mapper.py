"""Map risk/scoring inputs into RiskAssessment, InvalidationRule, and confidence."""

from __future__ import annotations

from models.decision import DecisionState
from models.risk import RiskAssessment
from models.signal import InvalidationRule
from risk.scoring.confidence_score import ConfidenceScore
from signal_engine.exceptions import SignalRiskAttachmentError


def confidence_value_from_score(score: ConfidenceScore) -> float:
    """Extract [0, 1] confidence. This is not a probability of profit."""
    value = float(score.value)
    if value < 0.0 or value > 1.0:
        raise SignalRiskAttachmentError("confidence must be between 0 and 1 inclusive")
    return value


def assert_directional_confidence(decision: DecisionState, confidence: float) -> None:
    """BUY/SELL require confidence > 0; HOLD may be zero."""
    if confidence < 0.0 or confidence > 1.0:
        raise SignalRiskAttachmentError("confidence must be between 0 and 1 inclusive")
    if decision in {DecisionState.BUY, DecisionState.SELL} and confidence <= 0.0:
        raise SignalRiskAttachmentError(
            "directional decisions require confidence > 0 "
            "(confidence is not a probability of profit)"
        )


def build_risk_assessment(
    *,
    exposure_impact: str,
    margin_impact: str | None = None,
    daily_loss_remaining_pct: float | None = None,
    position_limit_remaining_pct: float | None = None,
    notes: str | None = None,
) -> RiskAssessment:
    """Build RiskAssessment; exposure_impact is mandatory."""
    if not exposure_impact.strip():
        raise SignalRiskAttachmentError("exposure_impact must not be empty")
    return RiskAssessment(
        exposure_impact=exposure_impact.strip(),
        margin_impact=margin_impact.strip() if margin_impact else None,
        daily_loss_remaining_pct=daily_loss_remaining_pct,
        position_limit_remaining_pct=position_limit_remaining_pct,
        notes=notes.strip() if notes else None,
    )


def build_invalidation_rule(
    *,
    condition: str,
    price_level: float | None = None,
) -> InvalidationRule:
    """Build InvalidationRule from a human-readable condition."""
    if not condition.strip():
        raise SignalRiskAttachmentError("invalidation condition must not be empty")
    if price_level is not None and price_level <= 0:
        raise SignalRiskAttachmentError("invalidation price_level must be > 0")
    return InvalidationRule(condition=condition.strip(), price_level=price_level)


def invalidation_from_structure(
    decision: DecisionState,
    *,
    support: float | None = None,
    resistance: float | None = None,
) -> InvalidationRule:
    """Build invalidation from support/resistance structure levels when available."""
    if decision == DecisionState.BUY:
        if support is None or support <= 0:
            raise SignalRiskAttachmentError("BUY invalidation requires a positive support level")
        return build_invalidation_rule(
            condition=f"Break below support at {support:.6g}",
            price_level=support,
        )
    if decision == DecisionState.SELL:
        if resistance is None or resistance <= 0:
            raise SignalRiskAttachmentError(
                "SELL invalidation requires a positive resistance level"
            )
        return build_invalidation_rule(
            condition=f"Break above resistance at {resistance:.6g}",
            price_level=resistance,
        )
    return build_invalidation_rule(
        condition="Thesis is non-directional (HOLD); reassess on regime change.",
        price_level=None,
    )


def invalidation_from_atr(
    decision: DecisionState,
    *,
    current_price: float,
    atr: float,
    multiplier: float = 1.5,
) -> InvalidationRule:
    """ATR-anchored invalidation level (structural stop proxy, not advice)."""
    if current_price <= 0:
        raise SignalRiskAttachmentError("current_price must be > 0")
    if atr <= 0:
        raise SignalRiskAttachmentError("atr must be > 0")
    if multiplier <= 0:
        raise SignalRiskAttachmentError("multiplier must be > 0")
    offset = atr * multiplier
    if decision == DecisionState.BUY:
        level = current_price - offset
        if level <= 0:
            raise SignalRiskAttachmentError("ATR invalidation level must remain positive for BUY")
        return build_invalidation_rule(
            condition=(f"Close below ATR stop ({multiplier:g}x ATR) at {level:.6g}"),
            price_level=level,
        )
    if decision == DecisionState.SELL:
        level = current_price + offset
        return build_invalidation_rule(
            condition=(f"Close above ATR stop ({multiplier:g}x ATR) at {level:.6g}"),
            price_level=level,
        )
    return build_invalidation_rule(
        condition="HOLD: no ATR directional stop; reassess if ATR regime expands.",
        price_level=None,
    )
