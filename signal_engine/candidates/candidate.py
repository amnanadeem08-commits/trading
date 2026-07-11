"""Directional candidate DTO for statistical rules."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel
from models.decision import DecisionSource, DecisionState


class DirectionCandidate(PlatformModel):
    """Rule output ready to populate SignalAssemblyRequest decision fields."""

    decision: DecisionState
    decision_source: DecisionSource = DecisionSource.STATISTICAL_ONLY
    confidence: float = Field(ge=0.0, le=1.0)
    indicators_used: tuple[str, ...] = Field(min_length=1)
    indicator_values: dict[str, float | str | int | bool] = Field(min_length=1)
    rationale: str = Field(min_length=1)
