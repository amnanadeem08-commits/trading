"""Prediction validation service boundary."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from market_data.models.candle import Candle
from prediction_validation.contracts.config import PredictionValidationConfig
from prediction_validation.contracts.outcome import ValidationOutcomeRecord, ValidationStatus
from prediction_validation.contracts.prediction import PredictionRecord
from prediction_validation.contracts.summary import PredictionValidationSummary
from prediction_validation.engine.evaluator import evaluate_prediction_outcome
from prediction_validation.engine.metrics import compute_prediction_validation_summary
from prediction_validation.engine.store import PredictionValidationStore


class PredictionValidationService:
    """Record predictions and evaluate outcomes without mutating source records."""

    def __init__(
        self,
        *,
        store: PredictionValidationStore | None = None,
        config: PredictionValidationConfig | None = None,
    ) -> None:
        self._store = store or PredictionValidationStore()
        self._config = config or PredictionValidationConfig()

    @property
    def store(self) -> PredictionValidationStore:
        return self._store

    def record_prediction(self, prediction: PredictionRecord) -> PredictionRecord:
        """Append-only prediction recording with idempotent prediction_id."""
        return self._store.record_prediction(prediction)

    def evaluate_prediction(
        self,
        prediction_id: str,
        candles: Sequence[Candle],
        *,
        as_of: datetime,
    ) -> ValidationOutcomeRecord:
        """Evaluate and persist a terminal outcome; pending outcomes are not stored."""
        prediction = self._store.get_prediction(prediction_id)
        existing = self._store.get_outcome(prediction_id)
        if existing is not None:
            return existing

        outcome = evaluate_prediction_outcome(
            prediction,
            candles,
            as_of=as_of,
            config=self._config,
        )
        if outcome.status == ValidationStatus.PENDING:
            return outcome
        return self._store.record_outcome(outcome)

    def summarize(
        self,
        candles: Sequence[Candle],
        *,
        as_of: datetime,
    ) -> PredictionValidationSummary:
        """Compute summary including unresolved pending predictions at as_of."""
        predictions = self._store.list_predictions()
        stored_outcomes = self._store.list_outcomes()
        stored_by_id = {outcome.prediction_id: outcome for outcome in stored_outcomes}

        effective_outcomes: list[ValidationOutcomeRecord] = list(stored_outcomes)
        for prediction in predictions:
            if prediction.prediction_id in stored_by_id:
                continue
            evaluated = evaluate_prediction_outcome(
                prediction,
                candles,
                as_of=as_of,
                config=self._config,
            )
            if evaluated.status != ValidationStatus.PENDING:
                effective_outcomes.append(evaluated)

        return compute_prediction_validation_summary(
            predictions,
            tuple(effective_outcomes),
            config=self._config,
        )
