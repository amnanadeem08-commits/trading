"""Job contract for workflow orchestration."""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict, Field

from models.common import PlatformModel
from pipeline.stage import RetryPolicy


class Job(PlatformModel):
    """A managed job that executes a single pipeline."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    job_id: str = Field(min_length=1)
    pipeline_name: str = Field(min_length=1)
    priority: int = Field(default=0, ge=0)
    dependencies: tuple[str, ...] = Field(default_factory=tuple)
    timeout_seconds: int = Field(ge=1, default=300)
    retry_policy: RetryPolicy | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
