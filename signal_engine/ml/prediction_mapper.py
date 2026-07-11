"""Map inference-path outputs into MLPrediction contracts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from inference_pipeline.responses.inference_result import InferenceStatus
from inference_pipeline.runtime.inference_response import InferenceExecutionResponse
from models.common import VersionInfo
from models.prediction import MLPrediction, SignalDirection
from signal_engine.exceptions import SignalMLAttachmentError

_DIRECTION_KEYS = ("BUY", "SELL", "HOLD")


def _parse_direction(raw: object) -> SignalDirection:
    if isinstance(raw, SignalDirection):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        raise SignalMLAttachmentError("normalized_output.direction must be a non-empty string")
    try:
        return SignalDirection(raw.strip().upper())
    except ValueError as error:
        msg = f"Unsupported direction value: {raw!r}"
        raise SignalMLAttachmentError(msg) from error


def _parse_probabilities(raw: object) -> dict[str, float]:
    if not isinstance(raw, Mapping):
        raise SignalMLAttachmentError("direction_probabilities must be a mapping")
    probabilities: dict[str, float] = {}
    for key in _DIRECTION_KEYS:
        if key not in raw and key.lower() not in raw:
            msg = f"direction_probabilities missing key: {key}"
            raise SignalMLAttachmentError(msg)
        value = raw.get(key, raw.get(key.lower()))
        try:
            probabilities[key] = float(value)
        except (TypeError, ValueError) as error:
            msg = f"Invalid probability for {key}: {value!r}"
            raise SignalMLAttachmentError(msg) from error
        if probabilities[key] < 0.0 or probabilities[key] > 1.0:
            raise SignalMLAttachmentError(f"Probability out of range for {key}")
    return probabilities


def ml_prediction_from_normalized_output(
    normalized_output: Mapping[str, Any],
    *,
    model_name: str,
    model_version: VersionInfo | str,
    features_used: tuple[str, ...] = (),
    regime: str | None = None,
) -> MLPrediction:
    """Build MLPrediction from a normalized inference output mapping."""
    if not model_name.strip():
        raise SignalMLAttachmentError("model_name must not be empty")
    if "direction" not in normalized_output:
        raise SignalMLAttachmentError("normalized_output missing direction")
    if "direction_probabilities" not in normalized_output:
        raise SignalMLAttachmentError("normalized_output missing direction_probabilities")
    confidence_raw = normalized_output.get("ml_confidence", normalized_output.get("confidence"))
    if confidence_raw is None:
        raise SignalMLAttachmentError("normalized_output missing ml_confidence/confidence")
    try:
        ml_confidence = float(confidence_raw)
    except (TypeError, ValueError) as error:
        raise SignalMLAttachmentError(f"Invalid ml_confidence: {confidence_raw!r}") from error
    if ml_confidence < 0.0 or ml_confidence > 1.0:
        raise SignalMLAttachmentError("ml_confidence must be between 0 and 1")

    version = (
        model_version
        if isinstance(model_version, VersionInfo)
        else VersionInfo(version_id=str(model_version))
    )
    features = normalized_output.get("features_used", features_used)
    if isinstance(features, (list, tuple)):
        features_tuple = tuple(str(item) for item in features)
    else:
        features_tuple = features_used

    regime_value = regime
    if regime_value is None:
        raw_regime = normalized_output.get("regime")
        regime_value = str(raw_regime) if isinstance(raw_regime, str) else None

    return MLPrediction(
        direction=_parse_direction(normalized_output["direction"]),
        direction_probabilities=_parse_probabilities(normalized_output["direction_probabilities"]),
        ml_confidence=ml_confidence,
        model_name=model_name,
        model_version=version,
        features_used=features_tuple,
        regime=regime_value,
    )


def ml_prediction_from_inference_response(
    response: InferenceExecutionResponse,
    *,
    model_version: VersionInfo | str | None = None,
    features_used: tuple[str, ...] = (),
) -> MLPrediction:
    """Map a completed InferenceExecutionResponse into MLPrediction."""
    if response.status != InferenceStatus.COMPLETED:
        raise SignalMLAttachmentError(
            f"Inference status must be completed, got {response.status.value}"
        )
    if not response.normalized_output:
        raise SignalMLAttachmentError("Inference response normalized_output is empty")
    version: VersionInfo | str
    if model_version is not None:
        version = model_version
    else:
        raw_version = response.execution_attributes.get("model_version", "unknown")
        version = str(raw_version)
    return ml_prediction_from_normalized_output(
        response.normalized_output,
        model_name=response.model_id,
        model_version=version,
        features_used=features_used,
    )
