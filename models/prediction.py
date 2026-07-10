"""Prediction layer contracts. ML and AI outputs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, VersionInfo


class SignalDirection(StrEnum):
    """Directional signal from ML or statistical models."""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class StatisticalSignal(PlatformModel):
    """Output from statistical models layer."""

    direction: SignalDirection
    confidence: float = Field(ge=0.0, le=1.0)
    model_name: str = Field(min_length=1)
    model_version: VersionInfo
    features_used: tuple[str, ...]


class MLPrediction(PlatformModel):
    """Output from machine learning inference. Required input for AI layer."""

    direction: SignalDirection
    direction_probabilities: dict[str, float] = Field(
        description="Probability per direction, keys: BUY, SELL, HOLD"
    )
    ml_confidence: float = Field(ge=0.0, le=1.0)
    model_name: str = Field(min_length=1)
    model_version: VersionInfo
    features_used: tuple[str, ...]
    regime: str | None = None


class LLMInsight(PlatformModel):
    """Output from AI reasoning layer. Enhances ML — never replaces it."""

    reasoning: str = Field(min_length=1)
    alternative_scenario: str = Field(min_length=1)
    fomo_fear_note: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    prompt_version: VersionInfo
    ensemble_votes: dict[str, str] | None = Field(
        default=None,
        description="Optional multi-agent or multi-provider votes",
    )
