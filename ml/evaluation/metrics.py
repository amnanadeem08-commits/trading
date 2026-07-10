"""Evaluation metrics contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class EvaluationMetrics(PlatformModel):
    """Registered evaluation metrics for a model assessment."""

    evaluation_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    values: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)

    def register(self, name: str, value: float) -> EvaluationMetrics:
        """Register a metric value."""
        updated = dict(self.values)
        updated[name] = value
        return self.model_copy(update={"values": updated})
