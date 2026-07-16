"""Append-only prediction and validation stores."""

from __future__ import annotations

from threading import RLock

from prediction_validation.contracts.outcome import ValidationOutcomeRecord
from prediction_validation.contracts.prediction import PredictionRecord
from prediction_validation.exceptions import PredictionImmutableError, PredictionNotFoundError


class PredictionValidationStore:
    """Thread-safe append-only store for predictions and validation outcomes."""

    def __init__(self, *, max_predictions: int = 50_000) -> None:
        if max_predictions < 1:
            msg = "max_predictions must be >= 1"
            raise ValueError(msg)
        self._lock = RLock()
        self._max_predictions = max_predictions
        self._predictions: list[PredictionRecord] = []
        self._predictions_by_id: dict[str, PredictionRecord] = {}
        self._outcomes: list[ValidationOutcomeRecord] = []
        self._outcomes_by_prediction_id: dict[str, ValidationOutcomeRecord] = {}

    def record_prediction(self, prediction: PredictionRecord) -> PredictionRecord:
        """Append a prediction; return existing record when prediction_id already recorded."""
        with self._lock:
            existing = self._predictions_by_id.get(prediction.prediction_id)
            if existing is not None:
                if existing != prediction:
                    raise PredictionImmutableError(prediction.prediction_id)
                return existing
            if len(self._predictions) >= self._max_predictions:
                msg = f"Prediction store capacity exceeded: {self._max_predictions}"
                raise ValueError(msg)
            self._predictions.append(prediction)
            self._predictions_by_id[prediction.prediction_id] = prediction
            return prediction

    def record_outcome(self, outcome: ValidationOutcomeRecord) -> ValidationOutcomeRecord:
        """Append an outcome; return existing outcome when prediction_id already validated."""
        with self._lock:
            if outcome.prediction_id not in self._predictions_by_id:
                raise PredictionNotFoundError(outcome.prediction_id)
            existing = self._outcomes_by_prediction_id.get(outcome.prediction_id)
            if existing is not None:
                return existing
            self._outcomes.append(outcome)
            self._outcomes_by_prediction_id[outcome.prediction_id] = outcome
            return outcome

    def get_prediction(self, prediction_id: str) -> PredictionRecord:
        with self._lock:
            prediction = self._predictions_by_id.get(prediction_id)
            if prediction is None:
                raise PredictionNotFoundError(prediction_id)
            return prediction

    def get_outcome(self, prediction_id: str) -> ValidationOutcomeRecord | None:
        with self._lock:
            return self._outcomes_by_prediction_id.get(prediction_id)

    def list_predictions(self) -> tuple[PredictionRecord, ...]:
        with self._lock:
            return tuple(self._predictions)

    def list_outcomes(self) -> tuple[ValidationOutcomeRecord, ...]:
        with self._lock:
            return tuple(self._outcomes)
