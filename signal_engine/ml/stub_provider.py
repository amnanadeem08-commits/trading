"""Stub ML prediction provider for tests and local wiring."""

from __future__ import annotations

from models.common import VersionInfo
from models.prediction import MLPrediction, SignalDirection
from signal_engine.exceptions import SignalMLAttachmentError


class StubMLPredictionProvider:
    """Deterministic provider that always returns a configured prediction."""

    def __init__(self, prediction: MLPrediction | None = None, *, fail: bool = False) -> None:
        self._fail = fail
        self._prediction = prediction or MLPrediction(
            direction=SignalDirection.BUY,
            direction_probabilities={"BUY": 0.7, "SELL": 0.1, "HOLD": 0.2},
            ml_confidence=0.7,
            model_name="stub-model",
            model_version=VersionInfo(version_id="stub-1"),
            features_used=("rsi_14", "macd"),
        )

    def get_prediction(
        self,
        *,
        symbol_id: str,
        features: dict[str, float | str | int | bool],
    ) -> MLPrediction:
        if self._fail:
            raise SignalMLAttachmentError(f"stub provider forced failure for {symbol_id}")
        if not features:
            raise SignalMLAttachmentError("stub provider requires non-empty features")
        return self._prediction
