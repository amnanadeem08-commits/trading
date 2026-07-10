"""Predictor interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from ml.inference.inference_context import InferenceContext
from ml.inference.prediction_result import PredictionResult
from ml.models.model import MLModel


class Predictor(ABC):
    """Coordinates model inference operations."""

    @abstractmethod
    def predict(
        self,
        model: MLModel,
        *,
        inputs: tuple[dict[str, object], ...],
        context: InferenceContext | None = None,
    ) -> PredictionResult:
        """Run inference using a model implementation."""


class InMemoryPredictor(Predictor):
    """In-memory predictor for platform scaffolding."""

    def predict(
        self,
        model: MLModel,
        *,
        inputs: tuple[dict[str, object], ...],
        context: InferenceContext | None = None,
    ) -> PredictionResult:
        inference_id = context.inference_id if context is not None else str(uuid4())
        typed_inputs = tuple(dict(item) for item in inputs)
        result = model.predict(inputs=typed_inputs)
        return result.model_copy(
            update={
                "inference_id": inference_id,
                "model_id": model.model_id(),
                "model_version": model.version(),
            },
        )
