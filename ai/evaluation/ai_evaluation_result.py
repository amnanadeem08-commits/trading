"""AI evaluation result contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class AIEvaluationState(StrEnum):
    """Lifecycle states for AI evaluation."""

    CREATED = "created"
    COMPLETED = "completed"
    FAILED = "failed"


class AIEvaluationResult(PlatformModel):
    """Outcome of an AI evaluation operation."""

    evaluation_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    state: AIEvaluationState = AIEvaluationState.COMPLETED
    quality_score: float = Field(ge=0.0, le=1.0, default=0.0)
    metrics: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    errors: tuple[str, ...] = Field(default_factory=tuple)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
