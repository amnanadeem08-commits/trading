"""E2E integration: record prediction → evaluate outcome → summary."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from config.settings import get_settings, reset_settings
from models.prediction import SignalDirection
from prediction_validation import PredictionValidationService, ValidationStatus
from tests.prediction_validation.fixtures import make_candles, make_prediction


@pytest.fixture(autouse=True)
def _reset_globals():
    reset_settings()
    yield
    reset_settings()


@pytest.mark.integration
def test_prediction_validation_e2e_record_evaluate_summarize() -> None:
    settings = get_settings()
    assert settings.feature_flags.live_trading_enabled is False

    predicted_at = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    service = PredictionValidationService()
    prediction = make_prediction(
        prediction_id="e2e-1",
        direction=SignalDirection.BUY,
        predicted_at=predicted_at,
        signal_id="sig-e2e-1",
    )
    service.record_prediction(prediction)

    candles = make_candles([100.0, 108.0], start=predicted_at)
    as_of = predicted_at + timedelta(hours=1)
    outcome = service.evaluate_prediction(prediction.prediction_id, candles, as_of=as_of)

    assert outcome.status == ValidationStatus.VALIDATED
    assert outcome.is_directionally_correct is True
    summary = service.summarize(candles, as_of=as_of)
    assert summary.total_predictions == 1
    assert summary.validated == 1
    assert summary.correct == 1
    assert summary.directional_accuracy == pytest.approx(1.0)
