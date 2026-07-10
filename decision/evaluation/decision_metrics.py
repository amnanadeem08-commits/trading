"""Decision evaluation metrics."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class DecisionMetrics(PlatformModel):
    """Quality and consistency metrics for a decision result."""

    quality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    consistency_score: float = Field(ge=0.0, le=1.0, default=0.0)
    metadata: dict[str, str] = Field(default_factory=dict)
    details: dict[str, float] = Field(default_factory=dict)
