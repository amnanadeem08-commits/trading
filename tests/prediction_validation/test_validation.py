"""Prediction validation acceptance tests (VALIDATION-001)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from market_data.models.candle import Candle
from models.prediction import SignalDirection
from prediction_validation import (
    LookAheadValidationError,
    PredictionImmutableError,
    PredictionNotFoundError,
    PredictionValidationService,
    ValidationStatus,
    compute_prediction_validation_summary,
    evaluate_prediction_outcome,
)
from prediction_validation.contracts.config import PredictionValidationConfig
from prediction_validation.contracts.outcome import ValidationOutcomeRecord
from prediction_validation.engine.ids import validation_id_for_outcome
from prediction_validation.engine.store import PredictionValidationStore
from prediction_validation.contracts.prediction import PredictionRecord
from tests.prediction_validation.fixtures import make_candles, make_prediction


@pytest.mark.unit
def test_correct_bullish_prediction() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    prediction = make_prediction(
        prediction_id="bull-correct",
        direction=SignalDirection.BUY,
        predicted_at=predicted_at,
        reference_price=100.0,
        predicted_target=105.0,
        expected_move_pct=5.0,
    )
    candles = make_candles([100.0, 106.0], start=predicted_at)
    as_of = predicted_at + timedelta(hours=1)

    outcome = evaluate_prediction_outcome(prediction, candles, as_of=as_of)

    assert outcome.status == ValidationStatus.VALIDATED
    assert outcome.is_directionally_correct is True
    assert outcome.actual_price == pytest.approx(106.0)
    assert outcome.actual_move_pct == pytest.approx(6.0)
    assert outcome.move_error == pytest.approx(1.0)
    assert outcome.prediction_error_pct == pytest.approx(1.0)


@pytest.mark.unit
def test_incorrect_bullish_prediction() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    prediction = make_prediction(
        prediction_id="bull-wrong",
        direction=SignalDirection.BUY,
        predicted_at=predicted_at,
        reference_price=100.0,
    )
    candles = make_candles([100.0, 95.0], start=predicted_at)
    outcome = evaluate_prediction_outcome(
        prediction,
        candles,
        as_of=predicted_at + timedelta(hours=1),
    )

    assert outcome.status == ValidationStatus.VALIDATED
    assert outcome.is_directionally_correct is False
    assert outcome.actual_move_pct == pytest.approx(-5.0)


@pytest.mark.unit
def test_correct_bearish_prediction() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    prediction = make_prediction(
        prediction_id="bear-correct",
        direction=SignalDirection.SELL,
        predicted_at=predicted_at,
        reference_price=100.0,
        predicted_target=95.0,
        expected_move_pct=-5.0,
    )
    candles = make_candles([100.0, 94.0], start=predicted_at)
    outcome = evaluate_prediction_outcome(
        prediction,
        candles,
        as_of=predicted_at + timedelta(hours=1),
    )

    assert outcome.status == ValidationStatus.VALIDATED
    assert outcome.is_directionally_correct is True
    assert outcome.actual_move_pct == pytest.approx(-6.0)


@pytest.mark.unit
def test_pending_horizon_blocks_evaluation() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    prediction = make_prediction(predicted_at=predicted_at, horizon_bars=2)
    candles = make_candles([100.0, 101.0, 102.0], start=predicted_at)
    outcome = evaluate_prediction_outcome(
        prediction,
        candles,
        as_of=predicted_at + timedelta(hours=1),
    )

    assert outcome.status == ValidationStatus.PENDING
    assert outcome.actual_price is None
    assert outcome.is_directionally_correct is None


@pytest.mark.unit
def test_insufficient_future_data() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    prediction = make_prediction(predicted_at=predicted_at, horizon_bars=1)
    candles = make_candles([100.0], start=predicted_at)
    config = PredictionValidationConfig(max_wait_after_due=timedelta(hours=2))
    outcome = evaluate_prediction_outcome(
        prediction,
        candles,
        as_of=predicted_at + timedelta(hours=1),
        config=config,
    )

    assert outcome.status == ValidationStatus.INSUFFICIENT_DATA
    assert outcome.actual_price is None


@pytest.mark.unit
def test_expired_validation_when_wait_window_passes() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    prediction = make_prediction(predicted_at=predicted_at, horizon_bars=1)
    candles = make_candles([100.0], start=predicted_at)
    config = PredictionValidationConfig(max_wait_after_due=timedelta(hours=1))
    outcome = evaluate_prediction_outcome(
        prediction,
        candles,
        as_of=predicted_at + timedelta(hours=3),
        config=config,
    )

    assert outcome.status == ValidationStatus.EXPIRED


@pytest.mark.unit
def test_deterministic_repeated_validation() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    prediction = make_prediction(prediction_id="det-1", predicted_at=predicted_at)
    candles = make_candles([100.0, 103.0], start=predicted_at)
    as_of = predicted_at + timedelta(hours=1)

    first = evaluate_prediction_outcome(prediction, candles, as_of=as_of)
    second = evaluate_prediction_outcome(prediction, candles, as_of=as_of)

    assert first.model_dump() == second.model_dump()


@pytest.mark.unit
def test_duplicate_prediction_and_validation_prevention() -> None:
    service = PredictionValidationService()
    prediction = make_prediction(prediction_id="dup-1")
    candles = make_candles([100.0, 104.0], start=prediction.predicted_at)
    as_of = prediction.validation_due_at

    first_record = service.record_prediction(prediction)
    second_record = service.record_prediction(prediction)
    assert first_record is second_record

    first_outcome = service.evaluate_prediction(prediction.prediction_id, candles, as_of=as_of)
    second_outcome = service.evaluate_prediction(prediction.prediction_id, candles, as_of=as_of)
    assert first_outcome is second_outcome
    assert len(service.store.list_outcomes()) == 1


@pytest.mark.unit
def test_prediction_immutable_on_conflicting_rerecord() -> None:
    service = PredictionValidationService()
    prediction = make_prediction(prediction_id="immutable-1", confidence=0.8)
    service.record_prediction(prediction)
    conflicting = prediction.model_copy(update={"confidence": 0.5})
    with pytest.raises(PredictionImmutableError):
        service.record_prediction(conflicting)


@pytest.mark.unit
def test_no_look_ahead_blocks_future_candle() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    prediction = make_prediction(predicted_at=predicted_at, horizon_bars=1)
    as_of = predicted_at + timedelta(hours=1)
    gap_candles = (
        make_candles([100.0], start=predicted_at)[0],
        Candle(
            record_id="gap-future",
            dataset_id="crypto:binance",
            symbol_id="BTC/USDT",
            timestamp=predicted_at + timedelta(hours=2),
            open=110.0,
            high=111.0,
            low=109.0,
            close=110.0,
            volume=1.0,
            sequence=2,
        ),
    )
    with pytest.raises(LookAheadValidationError):
        evaluate_prediction_outcome(prediction, gap_candles, as_of=as_of)


@pytest.mark.unit
def test_prediction_contract_rejects_hold_and_invalid_due() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="HOLD"):
        make_prediction(direction=SignalDirection.HOLD)
    with pytest.raises(ValueError, match="validation_due_at"):
        PredictionRecord(
            prediction_id="bad-due",
            symbol_id="BTC/USDT",
            market_id="crypto:binance",
            timeframe="1h",
            predicted_at=predicted_at,
            prediction_horizon_bars=1,
            validation_due_at=predicted_at - timedelta(hours=1),
            predicted_direction=SignalDirection.BUY,
            confidence=0.5,
            model_reference="strategy-1",
            reference_price=100.0,
        )


@pytest.mark.unit
def test_store_errors_and_pending_service_paths() -> None:
    store = PredictionValidationStore(max_predictions=1)
    prediction = make_prediction(prediction_id="store-1")
    store.record_prediction(prediction)

    with pytest.raises(PredictionNotFoundError):
        store.get_prediction("missing")

    validated_at = datetime(2026, 1, 2, tzinfo=UTC)
    outcome = ValidationOutcomeRecord(
        validation_id=validation_id_for_outcome(
            prediction_id=prediction.prediction_id,
            status=ValidationStatus.INVALID.value,
            actual_price=None,
            validated_at_iso=validated_at.isoformat(),
        ),
        prediction_id=prediction.prediction_id,
        status=ValidationStatus.INVALID,
        validated_at=validated_at,
    )
    store.record_outcome(outcome)

    with pytest.raises(PredictionNotFoundError):
        store.record_outcome(
            outcome.model_copy(update={"prediction_id": "missing", "validation_id": "pvout-x"})
        )

    service = PredictionValidationService(store=store)
    pending = make_prediction(prediction_id="store-pending", horizon_bars=3)
    with pytest.raises(ValueError, match="capacity"):
        service.record_prediction(pending)

    pending_service = PredictionValidationService()
    pending_service.record_prediction(make_prediction(prediction_id="pending-sum", horizon_bars=3))
    candles = make_candles([100.0, 101.0], start=pending_service.store.list_predictions()[0].predicted_at)
    summary = pending_service.summarize(candles, as_of=candles[0].timestamp)
    assert summary.pending == 1


@pytest.mark.unit
def test_metrics_consistency() -> None:
    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    service = PredictionValidationService()
    bullish = make_prediction(
        prediction_id="m-bull",
        direction=SignalDirection.BUY,
        predicted_at=predicted_at,
        confidence=0.9,
    )
    bearish = make_prediction(
        prediction_id="m-bear",
        direction=SignalDirection.SELL,
        predicted_at=predicted_at + timedelta(hours=2),
        confidence=0.4,
    )
    service.record_prediction(bullish)
    service.record_prediction(bearish)

    candles = make_candles([100.0, 105.0, 100.0, 95.0], start=predicted_at)
    as_of = predicted_at + timedelta(hours=4)
    service.evaluate_prediction(bullish.prediction_id, candles, as_of=as_of)
    service.evaluate_prediction(bearish.prediction_id, candles, as_of=as_of)

    summary = service.summarize(candles, as_of=as_of)
    recomputed = compute_prediction_validation_summary(
        service.store.list_predictions(),
        service.store.list_outcomes(),
    )

    assert summary.total_predictions == 2
    assert summary.validated == 2
    assert summary.correct == 2
    assert summary.incorrect == 0
    assert summary.directional_accuracy == pytest.approx(1.0)
    assert summary.average_confidence == pytest.approx(0.65)
    assert summary == recomputed
    assert summary.calibration_buckets

    expired_summary = compute_prediction_validation_summary(
        (bullish,),
        (
            ValidationOutcomeRecord(
                validation_id="pvout-exp",
                prediction_id=bullish.prediction_id,
                status=ValidationStatus.EXPIRED,
            ),
        ),
    )
    assert expired_summary.expired == 1
    assert expired_summary.pending == 0
