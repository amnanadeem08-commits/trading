"""Training result contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ml.training.training_job import TrainingJobState
from models.common import PlatformModel, UTCDateTime, utc_now


class TrainingResult(PlatformModel):
    """Outcome of a training operation."""

    job_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    dataset_id: str = Field(min_length=1)
    state: TrainingJobState
    artifact_uri: str = Field(min_length=1, default="memory://artifact")
    metrics: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    errors: tuple[str, ...] = Field(default_factory=tuple)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
    output: dict[str, Any] = Field(default_factory=dict)
