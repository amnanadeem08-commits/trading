"""Map ExplainableSignal into PaperOrderRequest with explicit reject reasons."""

from __future__ import annotations

from uuid import uuid4

from models.decision import DecisionSource, DecisionState
from models.signal import ExplainableSignal
from paper_trading.contracts.paper_order import (
    PaperOrderMappingResult,
    PaperOrderRequest,
    PaperOrderSide,
)
from paper_trading.exceptions import PaperMappingError

_PRICE_KEYS: tuple[str, ...] = ("close", "price", "reference_price", "last")


def _side_from_decision(decision: DecisionState) -> PaperOrderSide:
    if decision == DecisionState.BUY:
        return PaperOrderSide.BUY
    if decision == DecisionState.SELL:
        return PaperOrderSide.SELL
    return PaperOrderSide.FLAT


def _optional_positive_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return number if number > 0 else None
    if isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
        return number if number > 0 else None
    return None


def reference_price_from_signal(signal: ExplainableSignal) -> float | None:
    """Extract reference price from indicator_values when market context provides it."""
    for key in _PRICE_KEYS:
        price = _optional_positive_float(signal.indicator_values.get(key))
        if price is not None:
            return price
    return None


def map_signal_to_paper_order(
    signal: ExplainableSignal,
    *,
    session_id: str,
    request_id: str | None = None,
    quantity: float | None = None,
    require_reference_price_for_directional: bool = True,
) -> PaperOrderMappingResult:
    """Map a signal to a paper order request, or return explicit rejection reasons."""
    reasons: list[str] = []

    if not session_id.strip():
        reasons.append("session_id must not be empty")
    if not signal.signal_id.strip():
        reasons.append("signal_id must not be empty")
    if not signal.symbol_id.strip():
        reasons.append("symbol_id must not be empty")
    if not signal.market_id.strip():
        reasons.append("market_id must not be empty")
    if not signal.indicators_used:
        reasons.append("indicators_used must not be empty")
    if not signal.indicator_values:
        reasons.append("indicator_values must not be empty")
    if not signal.risk_assessment.exposure_impact.strip():
        reasons.append("risk_assessment.exposure_impact is required")
    if not signal.invalidation.condition.strip():
        reasons.append("invalidation.condition is required")
    if signal.decision in {DecisionState.BUY, DecisionState.SELL} and signal.confidence <= 0:
        reasons.append("directional decisions require confidence > 0")
    if signal.decision_source == DecisionSource.AI_ENHANCED_ML and signal.llm_insight is None:
        reasons.append("llm_insight required when decision_source is ai_enhanced_ml")
    if (
        signal.decision_source in {DecisionSource.AI_ENHANCED_ML, DecisionSource.ML_ONLY}
        and signal.ml_prediction is None
    ):
        reasons.append("ml_prediction required for ai_enhanced_ml and ml_only sources")

    reference_price = reference_price_from_signal(signal)
    if (
        require_reference_price_for_directional
        and signal.decision in {DecisionState.BUY, DecisionState.SELL}
        and reference_price is None
    ):
        reasons.append(
            "reference price required from market context "
            f"(indicator_values keys: {', '.join(_PRICE_KEYS)})"
        )

    if quantity is not None and quantity <= 0:
        reasons.append("quantity must be > 0 when provided")

    if reasons:
        return PaperOrderMappingResult(passed=False, reasons=tuple(reasons), order=None)

    resolved_request_id = request_id.strip() if request_id else f"paper-req-{uuid4()}"
    side = _side_from_decision(signal.decision)
    order = PaperOrderRequest(
        request_id=resolved_request_id,
        session_id=session_id.strip(),
        signal_id=signal.signal_id,
        symbol_id=signal.symbol_id,
        market_id=signal.market_id,
        side=side,
        decision=signal.decision,
        decision_source=signal.decision_source,
        confidence=signal.confidence,
        reference_price=reference_price,
        quantity=quantity,
        invalidation_condition=signal.invalidation.condition,
        risk_exposure_impact=signal.risk_assessment.exposure_impact,
        prompt_version=signal.provenance.prompt_version,
        feature_snapshot_version=signal.provenance.feature_snapshot_version,
        adapter_payload={
            "signal_id": signal.signal_id,
            "symbol_id": signal.symbol_id,
            "market_id": signal.market_id,
            "side": side.value,
            "decision": signal.decision.value,
            "confidence": signal.confidence,
            "reference_price": reference_price,
            "simulated": True,
            "live_broker": False,
        },
        metadata={
            "path": "paper",
            "decision_source": signal.decision_source.value,
            "note": "simulated_only_not_financial_advice",
        },
    )
    return PaperOrderMappingResult(passed=True, reasons=(), order=order)


def paper_order_from_signal(
    signal: ExplainableSignal,
    *,
    session_id: str,
    request_id: str | None = None,
    quantity: float | None = None,
    require_reference_price_for_directional: bool = True,
) -> PaperOrderRequest:
    """Map signal to PaperOrderRequest or raise PaperMappingError with reasons."""
    result = map_signal_to_paper_order(
        signal,
        session_id=session_id,
        request_id=request_id,
        quantity=quantity,
        require_reference_price_for_directional=require_reference_price_for_directional,
    )
    if not result.passed or result.order is None:
        raise PaperMappingError(
            "Signal rejected for paper order mapping",
            reasons=result.reasons,
        )
    return result.order
