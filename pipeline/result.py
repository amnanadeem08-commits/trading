"""Pipeline and stage result models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class PipelineStatus(StrEnum):
    """Overall pipeline execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"


class StageStatus(StrEnum):
    """Individual stage execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class StageResult(PlatformModel):
    """Result of a single stage execution."""

    stage_name: str = Field(min_length=1)
    stage_version: str = Field(min_length=1)
    status: StageStatus
    message: str = Field(min_length=1)
    duration_ms: float = Field(ge=0.0, default=0.0)
    metrics: dict[str, Any] = Field(default_factory=dict)
    started_at: UTCDateTime = Field(default_factory=utc_now)
    completed_at: UTCDateTime | None = None


class PipelineResult(PlatformModel):
    """Aggregate result of a pipeline execution."""

    pipeline_name: str = Field(min_length=1)
    status: PipelineStatus
    errors: tuple[str, ...] = Field(default_factory=tuple)
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    metrics: dict[str, Any] = Field(default_factory=dict)
    timings: dict[str, float] = Field(default_factory=dict)
    stage_results: tuple[StageResult, ...] = Field(default_factory=tuple)
    started_at: UTCDateTime = Field(default_factory=utc_now)
    completed_at: UTCDateTime | None = None
