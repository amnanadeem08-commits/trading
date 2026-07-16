"""Aggregate prediction validation metrics."""

from __future__ import annotations

from prediction_validation.contracts.config import PredictionValidationConfig
from prediction_validation.contracts.outcome import ValidationOutcomeRecord, ValidationStatus
from prediction_validation.contracts.prediction import PredictionRecord
from prediction_validation.contracts.summary import (
    ConfidenceCalibrationBucket,
    PredictionValidationSummary,
)

def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _bucket_label(*, confidence: float, bucket_size: float) -> str:
    index = min(int(confidence / bucket_size), int(1.0 / bucket_size) - 1)
    lower = index * bucket_size
    upper = lower + bucket_size
    return f"{lower:.1f}-{upper:.1f}"


def compute_prediction_validation_summary(
    predictions: tuple[PredictionRecord, ...],
    outcomes: tuple[ValidationOutcomeRecord, ...],
    *,
    config: PredictionValidationConfig | None = None,
) -> PredictionValidationSummary:
    """Aggregate deterministic metrics from predictions and stored outcomes."""
    cfg = config or PredictionValidationConfig()
    outcome_by_prediction = {outcome.prediction_id: outcome for outcome in outcomes}

    pending = 0
    validated = 0
    expired = 0
    insufficient = 0
    invalid = 0
    correct = 0
    incorrect = 0

    confidences: list[float] = []
    confidences_correct: list[float] = []
    confidences_incorrect: list[float] = []
    realized_moves: list[float] = []
    prediction_errors: list[float] = []
    bucket_totals: dict[str, list[bool]] = {}

    for prediction in predictions:
        confidences.append(prediction.confidence)
        outcome = outcome_by_prediction.get(prediction.prediction_id)
        if outcome is None:
            pending += 1
            continue

        if outcome.status == ValidationStatus.PENDING:
            pending += 1
        elif outcome.status == ValidationStatus.VALIDATED:
            validated += 1
            if outcome.is_directionally_correct is True:
                correct += 1
                confidences_correct.append(prediction.confidence)
            elif outcome.is_directionally_correct is False:
                incorrect += 1
                confidences_incorrect.append(prediction.confidence)
            if outcome.actual_move_pct is not None:
                realized_moves.append(outcome.actual_move_pct)
            if outcome.prediction_error_pct is not None:
                prediction_errors.append(outcome.prediction_error_pct)
            label = _bucket_label(confidence=prediction.confidence, bucket_size=cfg.calibration_bucket_size)
            bucket = bucket_totals.setdefault(label, [])
            bucket.append(outcome.is_directionally_correct is True)
        elif outcome.status == ValidationStatus.EXPIRED:
            expired += 1
        elif outcome.status == ValidationStatus.INSUFFICIENT_DATA:
            insufficient += 1
        elif outcome.status == ValidationStatus.INVALID:
            invalid += 1

    directional_accuracy: float | None = None
    decided = correct + incorrect
    if decided > 0:
        directional_accuracy = correct / decided

    calibration_buckets: list[ConfidenceCalibrationBucket] = []
    for label in sorted(bucket_totals):
        values = bucket_totals[label]
        bucket_correct = sum(1 for value in values if value)
        total = len(values)
        accuracy = bucket_correct / total if total else None
        calibration_buckets.append(
            ConfidenceCalibrationBucket(
                bucket_label=label,
                total=total,
                correct=bucket_correct,
                accuracy=accuracy,
            )
        )

    return PredictionValidationSummary(
        total_predictions=len(predictions),
        pending=pending,
        validated=validated,
        expired=expired,
        insufficient_data=insufficient,
        invalid=invalid,
        correct=correct,
        incorrect=incorrect,
        directional_accuracy=directional_accuracy,
        average_confidence=_average(confidences),
        average_confidence_correct=_average(confidences_correct),
        average_confidence_incorrect=_average(confidences_incorrect),
        calibration_buckets=tuple(calibration_buckets),
        average_realized_move_pct=_average(realized_moves),
        average_prediction_error_pct=_average(prediction_errors),
    )
