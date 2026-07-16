"""Fixed candle fixtures for prediction validation tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from market_data.models.candle import Candle
from models.prediction import SignalDirection
from prediction_validation import PredictionRecord


def make_candles(
    closes: list[float],
    *,
    symbol_id: str = "BTC/USDT",
    dataset_id: str = "crypto:binance",
    start: datetime | None = None,
    interval: timedelta = timedelta(hours=1),
) -> tuple[Candle, ...]:
    base = start or datetime(2026, 1, 1, tzinfo=UTC)
    candles: list[Candle] = []
    for index, close in enumerate(closes):
        candles.append(
            Candle(
                record_id=f"pv-c-{index}",
                dataset_id=dataset_id,
                symbol_id=symbol_id,
                timestamp=base + interval * index,
                open=close,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=100.0,
                sequence=index,
            )
        )
    return tuple(candles)


def make_prediction(
    *,
    prediction_id: str = "pred-001",
    signal_id: str | None = "sig-001",
    direction: SignalDirection = SignalDirection.BUY,
    predicted_at: datetime | None = None,
    horizon_bars: int = 1,
    interval: timedelta = timedelta(hours=1),
    reference_price: float = 100.0,
    predicted_target: float | None = 105.0,
    expected_move_pct: float | None = 5.0,
    confidence: float = 0.75,
    model_reference: str = "strategy-1.0.0",
) -> PredictionRecord:
    base = predicted_at or datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    return PredictionRecord(
        prediction_id=prediction_id,
        signal_id=signal_id,
        symbol_id="BTC/USDT",
        market_id="crypto:binance",
        timeframe="1h",
        predicted_at=base,
        prediction_horizon_bars=horizon_bars,
        validation_due_at=base + interval * horizon_bars,
        predicted_direction=direction,
        predicted_target=predicted_target,
        expected_move_pct=expected_move_pct,
        confidence=confidence,
        model_reference=model_reference,
        reference_price=reference_price,
    )
