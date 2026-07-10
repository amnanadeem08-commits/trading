"""Evaluator interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from ml.evaluation.evaluation_result import EvaluationResult, EvaluationState
from ml.evaluation.metrics import EvaluationMetrics
from ml.models.model import MLModel


class Evaluator(ABC):
    """Coordinates model evaluation operations."""

    @abstractmethod
    def evaluate(
        self,
        model: MLModel,
        *,
        dataset_id: str,
        predictions: tuple[dict[str, object], ...],
    ) -> EvaluationResult:
        """Evaluate model outputs against a dataset reference."""


class InMemoryEvaluator(Evaluator):
    """In-memory evaluator for platform scaffolding."""

    def evaluate(
        self,
        model: MLModel,
        *,
        dataset_id: str,
        predictions: tuple[dict[str, object], ...],
    ) -> EvaluationResult:
        evaluation_id = str(uuid4())
        typed_predictions = tuple(dict(item) for item in predictions)
        try:
            result = model.evaluate(dataset_id=dataset_id, predictions=typed_predictions)
            return result
        except NotImplementedError:
            metrics = EvaluationMetrics(
                evaluation_id=evaluation_id,
                model_id=model.model_id(),
            ).register("record_count", float(len(typed_predictions)))
            return EvaluationResult(
                evaluation_id=evaluation_id,
                model_id=model.model_id(),
                dataset_id=dataset_id,
                state=EvaluationState.COMPLETED,
                metrics=metrics,
            )
        except Exception as error:
            metrics = EvaluationMetrics(
                evaluation_id=evaluation_id,
                model_id=model.model_id(),
            )
            return EvaluationResult(
                evaluation_id=evaluation_id,
                model_id=model.model_id(),
                dataset_id=dataset_id,
                state=EvaluationState.FAILED,
                metrics=metrics,
                errors=(str(error),),
            )
