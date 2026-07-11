"""Prediction provider port for dependency inversion."""

from __future__ import annotations

from typing import Protocol

from models.prediction import MLPrediction


class MLPredictionProvider(Protocol):
    """Callable port that yields an MLPrediction for signal assembly."""

    def get_prediction(
        self,
        *,
        symbol_id: str,
        features: dict[str, float | str | int | bool],
    ) -> MLPrediction:
        """Return a prediction or raise on failure (never return silently empty)."""
