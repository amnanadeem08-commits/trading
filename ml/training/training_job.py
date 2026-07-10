"""Training job contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from core.context.core_context import CoreContext
from models.common import PlatformModel, UTCDateTime, utc_now


class TrainingJobState(StrEnum):
    """Lifecycle states for training jobs."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


TERMINAL_TRAINING_STATES: frozenset[TrainingJobState] = frozenset(
    {
        TrainingJobState.COMPLETED,
        TrainingJobState.FAILED,
    }
)


class TrainingContext(PlatformModel):
    """Context for a training operation."""

    job_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    core_context: CoreContext | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class TrainingJob(PlatformModel):
    """Registered training job definition."""

    job_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    state: TrainingJobState = TrainingJobState.CREATED
    parameters: dict[str, Any] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)
    started_at: UTCDateTime | None = None
    completed_at: UTCDateTime | None = None
    error_message: str | None = None
