"""Attach confidence, RiskAssessment, and InvalidationRule onto assembly requests."""

from __future__ import annotations

from models.decision import DecisionState
from models.risk import RiskAssessment
from models.signal import InvalidationRule
from risk.scoring.confidence_score import ConfidenceScore
from signal_engine.contracts.assembly_request import SignalAssemblyRequest
from signal_engine.exceptions import SignalRiskAttachmentError
from signal_engine.risk.risk_mapper import (
    assert_directional_confidence,
    confidence_value_from_score,
)
from signal_engine.risk.risk_port import RiskBindingProvider


def attach_confidence(
    request: SignalAssemblyRequest,
    confidence: float | ConfidenceScore,
    *,
    decision: DecisionState | None = None,
) -> SignalAssemblyRequest:
    """Bind confidence onto the request. Confidence is not a probability of profit."""
    value = (
        confidence_value_from_score(confidence)
        if isinstance(confidence, ConfidenceScore)
        else float(confidence)
    )
    bound_decision = decision if decision is not None else request.decision
    assert_directional_confidence(bound_decision, value)
    updates: dict[str, object] = {"confidence": value}
    if decision is not None:
        updates["decision"] = decision
    attached = request.model_copy(update=updates)
    ensure_risk_bindings_present(attached, require_confidence_only=True)
    return attached


def attach_risk_assessment(
    request: SignalAssemblyRequest,
    assessment: RiskAssessment,
) -> SignalAssemblyRequest:
    """Attach a risk assessment narrative."""
    if not assessment.exposure_impact.strip():
        raise SignalRiskAttachmentError("exposure_impact must not be empty")
    return request.model_copy(update={"risk_assessment": assessment})


def attach_invalidation(
    request: SignalAssemblyRequest,
    rule: InvalidationRule,
) -> SignalAssemblyRequest:
    """Attach an invalidation rule."""
    if not rule.condition.strip():
        raise SignalRiskAttachmentError("invalidation condition must not be empty")
    return request.model_copy(update={"invalidation": rule})


def attach_risk_bindings(
    request: SignalAssemblyRequest,
    *,
    confidence: float | ConfidenceScore,
    assessment: RiskAssessment,
    invalidation: InvalidationRule,
    decision: DecisionState | None = None,
) -> SignalAssemblyRequest:
    """Bind confidence, risk assessment, and invalidation together."""
    updated = attach_confidence(request, confidence, decision=decision)
    updated = attach_risk_assessment(updated, assessment)
    updated = attach_invalidation(updated, invalidation)
    ensure_risk_bindings_present(updated)
    return updated


def attach_risk_bindings_from_provider(
    request: SignalAssemblyRequest,
    provider: RiskBindingProvider,
) -> SignalAssemblyRequest:
    """Resolve confidence/risk/invalidation from a provider port and attach them."""
    try:
        score = provider.get_confidence(
            symbol_id=request.symbol_id,
            decision=request.decision,
            indicator_values=dict(request.indicator_values),
        )
        confidence = confidence_value_from_score(score)
        assessment = provider.get_assessment(
            symbol_id=request.symbol_id,
            decision=request.decision,
            confidence=confidence,
            indicator_values=dict(request.indicator_values),
        )
        invalidation = provider.get_invalidation(
            decision=request.decision,
            indicator_values=dict(request.indicator_values),
        )
    except SignalRiskAttachmentError:
        raise
    except Exception as error:
        msg = f"Risk binding provider failed: {error}"
        raise SignalRiskAttachmentError(msg) from error
    return attach_risk_bindings(
        request,
        confidence=confidence,
        assessment=assessment,
        invalidation=invalidation,
    )


def ensure_risk_bindings_present(
    request: SignalAssemblyRequest,
    *,
    require_confidence_only: bool = False,
) -> None:
    """Fail explicitly when required risk bindings are missing or invalid."""
    assert_directional_confidence(request.decision, request.confidence)
    if require_confidence_only:
        return
    if not request.risk_assessment.exposure_impact.strip():
        raise SignalRiskAttachmentError("risk_assessment.exposure_impact is required")
    if not request.invalidation.condition.strip():
        raise SignalRiskAttachmentError("invalidation.condition is required")
