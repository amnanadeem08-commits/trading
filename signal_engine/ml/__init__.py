"""ML attachment package exports."""

from __future__ import annotations

from signal_engine.exceptions import SignalMLAttachmentError
from signal_engine.ml.attach import (
    attach_ml_prediction,
    attach_ml_prediction_from_provider,
    ensure_ml_prediction_present,
)
from signal_engine.ml.prediction_mapper import (
    ml_prediction_from_inference_response,
    ml_prediction_from_normalized_output,
)
from signal_engine.ml.prediction_port import MLPredictionProvider
from signal_engine.ml.stub_provider import StubMLPredictionProvider

__all__ = [
    "MLPredictionProvider",
    "SignalMLAttachmentError",
    "StubMLPredictionProvider",
    "attach_ml_prediction",
    "attach_ml_prediction_from_provider",
    "ensure_ml_prediction_present",
    "ml_prediction_from_inference_response",
    "ml_prediction_from_normalized_output",
]
