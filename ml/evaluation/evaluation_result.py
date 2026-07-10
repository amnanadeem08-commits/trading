"""Evaluation result contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ml.evaluation.metrics import EvaluationMetrics
from models.common import PlatformModel, UTCDateTime, utc_now


class EvaluationState(StrEnum):
    """Lifecycle states for evaluation operations."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationResult(PlatformModel):
    """Outcome of a model evaluation operation."""

    evaluation_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    state: EvaluationState = EvaluationState.COMPLETED
    metrics: EvaluationMetrics
    errors: tuple[str, ...] = Field(default_factory=tuple)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
