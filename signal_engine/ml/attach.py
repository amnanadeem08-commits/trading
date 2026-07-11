"""Attach MLPrediction onto SignalAssemblyRequest."""

from __future__ import annotations

from models.decision import DecisionSource, DecisionState
from models.prediction import MLPrediction, SignalDirection
from signal_engine.contracts.assembly_request import SignalAssemblyRequest
from signal_engine.exceptions import SignalMLAttachmentError
from signal_engine.ml.prediction_port import MLPredictionProvider


def _direction_to_decision(direction: SignalDirection) -> DecisionState:
    if direction == SignalDirection.BUY:
        return DecisionState.BUY
    if direction == SignalDirection.SELL:
        return DecisionState.SELL
    return DecisionState.HOLD


def attach_ml_prediction(
    request: SignalAssemblyRequest,
    prediction: MLPrediction,
    *,
    decision_source: DecisionSource = DecisionSource.ML_ONLY,
    update_decision_from_prediction: bool = True,
) -> SignalAssemblyRequest:
    """Attach prediction to the request. Never silently drops required prediction."""
    if decision_source not in {
        DecisionSource.ML_ONLY,
        DecisionSource.AI_ENHANCED_ML,
    }:
        raise SignalMLAttachmentError(
            "decision_source must be ml_only or ai_enhanced_ml when attaching ML prediction"
        )

    updates: dict[str, object] = {
        "ml_prediction": prediction,
        "decision_source": decision_source,
        "confidence": prediction.ml_confidence,
    }
    if update_decision_from_prediction:
        updates["decision"] = _direction_to_decision(prediction.direction)
    attached = request.model_copy(update=updates)
    ensure_ml_prediction_present(attached)
    return attached


def attach_ml_prediction_from_provider(
    request: SignalAssemblyRequest,
    provider: MLPredictionProvider,
    *,
    decision_source: DecisionSource = DecisionSource.ML_ONLY,
) -> SignalAssemblyRequest:
    """Resolve prediction from a provider port and attach it."""
    try:
        prediction = provider.get_prediction(
            symbol_id=request.symbol_id,
            features=dict(request.indicator_values),
        )
    except SignalMLAttachmentError:
        raise
    except Exception as error:
        msg = f"ML prediction provider failed: {error}"
        raise SignalMLAttachmentError(msg) from error
    return attach_ml_prediction(
        request,
        prediction,
        decision_source=decision_source,
    )


def ensure_ml_prediction_present(request: SignalAssemblyRequest) -> None:
    """Fail explicitly when ML sources are missing an attached prediction."""
    if (
        request.decision_source
        in {
            DecisionSource.ML_ONLY,
            DecisionSource.AI_ENHANCED_ML,
        }
        and request.ml_prediction is None
    ):
        raise SignalMLAttachmentError(
            "ml_prediction is required for ml_only and ai_enhanced_ml decision sources"
        )
