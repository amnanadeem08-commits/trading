"""Deterministic prediction outcome evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from market_data.models.candle import Candle
from models.prediction import SignalDirection
from prediction_validation.contracts.config import PredictionValidationConfig
from prediction_validation.contracts.outcome import ValidationOutcomeRecord, ValidationStatus
from prediction_validation.contracts.prediction import PredictionRecord
from prediction_validation.engine.candle_resolver import resolve_outcome_candle
from prediction_validation.engine.ids import validation_id_for_outcome


def _move_pct(*, reference_price: float, actual_price: float) -> float:
    return (actual_price - reference_price) / reference_price * 100.0


def _directionally_correct(
    *,
    predicted_direction: SignalDirection,
    reference_price: float,
    actual_price: float,
) -> bool:
    if predicted_direction == SignalDirection.BUY:
        return actual_price > reference_price
    if predicted_direction == SignalDirection.SELL:
        return actual_price < reference_price
    return False


def _pending_outcome(prediction: PredictionRecord) -> ValidationOutcomeRecord:
    return ValidationOutcomeRecord(
        validation_id=validation_id_for_outcome(
            prediction_id=prediction.prediction_id,
            status=ValidationStatus.PENDING.value,
            actual_price=None,
            validated_at_iso=prediction.validation_due_at.isoformat(),
        ),
        prediction_id=prediction.prediction_id,
        status=ValidationStatus.PENDING,
        validation_notes=("Horizon not complete; evaluation blocked until validation_due_at.",),
    )


def evaluate_prediction_outcome(
    prediction: PredictionRecord,
    candles: Sequence[Candle],
    *,
    as_of: datetime,
    config: PredictionValidationConfig | None = None,
) -> ValidationOutcomeRecord:
    """Evaluate one prediction using market data available at or after due time."""
    cfg = config or PredictionValidationConfig()

    if as_of < prediction.validation_due_at:
        return _pending_outcome(prediction)

    outcome_candle = resolve_outcome_candle(
        candles,
        validation_due_at=prediction.validation_due_at,
        as_of=as_of,
    )
    if outcome_candle is None:
        validated_at = as_of
        if as_of >= prediction.validation_due_at + cfg.max_wait_after_due:
            status = ValidationStatus.EXPIRED
            note = "Validation window expired before outcome data became available."
        else:
            status = ValidationStatus.INSUFFICIENT_DATA
            note = "No market data at or after validation due timestamp within as_of window."
        return ValidationOutcomeRecord(
            validation_id=validation_id_for_outcome(
                prediction_id=prediction.prediction_id,
                status=status.value,
                actual_price=None,
                validated_at_iso=validated_at.isoformat(),
            ),
            prediction_id=prediction.prediction_id,
            status=status,
            validated_at=validated_at,
            validation_notes=(note,),
        )

    actual_price = float(outcome_candle.close)
    actual_move = _move_pct(reference_price=prediction.reference_price, actual_price=actual_price)
    correct = _directionally_correct(
        predicted_direction=prediction.predicted_direction,
        reference_price=prediction.reference_price,
        actual_price=actual_price,
    )

    move_error: float | None = None
    if prediction.predicted_target is not None:
        move_error = abs(actual_price - prediction.predicted_target)

    prediction_error_pct: float | None = None
    if prediction.expected_move_pct is not None:
        prediction_error_pct = abs(actual_move - prediction.expected_move_pct)

    validated_at = outcome_candle.timestamp
    return ValidationOutcomeRecord(
        validation_id=validation_id_for_outcome(
            prediction_id=prediction.prediction_id,
            status=ValidationStatus.VALIDATED.value,
            actual_price=actual_price,
            validated_at_iso=validated_at.isoformat(),
        ),
        prediction_id=prediction.prediction_id,
        status=ValidationStatus.VALIDATED,
        actual_price=actual_price,
        actual_move_pct=actual_move,
        is_directionally_correct=correct,
        move_error=move_error,
        prediction_error_pct=prediction_error_pct,
        validated_at=validated_at,
        validation_notes=(),
    )
