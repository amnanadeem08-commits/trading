"""Helpers for ML layer tests."""

from __future__ import annotations

from typing import Any

from ml.evaluation.evaluation_result import EvaluationResult, EvaluationState
from ml.evaluation.metrics import EvaluationMetrics
from ml.inference.prediction_result import PredictionResult
from ml.models.model import MLModel
from ml.models.model_metadata import ModelMetadata
from ml.training.training_job import TrainingJobState
from ml.training.training_result import TrainingResult


def make_model_metadata(
    *,
    model_id: str = "sample-model",
    name: str = "Sample Model",
    version: str = "1.0.0",
) -> ModelMetadata:
    return ModelMetadata(
        model_id=model_id,
        name=name,
        version=version,
        framework="platform",
        tags=("test",),
    )


class SampleMLModel(MLModel):
    """Concrete ML model used in unit tests."""

    def model_id(self) -> str:
        return "sample-model"

    def name(self) -> str:
        return "Sample Model"

    def version(self) -> str:
        return "1.0.0"

    def train(self, *, dataset_id: str, parameters: dict[str, Any]) -> TrainingResult:
        return TrainingResult(
            job_id="job-sample",
            model_id=self.model_id(),
            dataset_id=dataset_id,
            state=TrainingJobState.COMPLETED,
            metrics={"loss": 0.1},
            output={"epochs": parameters.get("epochs", 1)},
        )

    def predict(self, *, inputs: tuple[dict[str, Any], ...]) -> PredictionResult:
        outputs = tuple({"score": 0.9, **record} for record in inputs)
        return PredictionResult(
            inference_id="inf-sample",
            model_id=self.model_id(),
            model_version=self.version(),
            outputs=outputs,
            metadata={"count": str(len(inputs))},
        )

    def evaluate(
        self,
        *,
        dataset_id: str,
        predictions: tuple[dict[str, Any], ...],
    ) -> EvaluationResult:
        metrics = EvaluationMetrics(
            evaluation_id="eval-sample",
            model_id=self.model_id(),
        ).register("accuracy", 0.95)
        return EvaluationResult(
            evaluation_id="eval-sample",
            model_id=self.model_id(),
            dataset_id=dataset_id,
            state=EvaluationState.COMPLETED,
            metrics=metrics,
        )


class FailingMLModel(MLModel):
    """Model that fails during training."""

    def model_id(self) -> str:
        return "failing-model"

    def name(self) -> str:
        return "Failing Model"

    def version(self) -> str:
        return "1.0.0"

    def train(self, *, dataset_id: str, parameters: dict[str, Any]) -> TrainingResult:
        raise RuntimeError("training failed")

    def predict(self, *, inputs: tuple[dict[str, Any], ...]) -> PredictionResult:
        return PredictionResult(
            inference_id="inf-fail",
            model_id=self.model_id(),
            model_version=self.version(),
        )
