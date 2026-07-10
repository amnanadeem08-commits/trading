"""Workflow execution result models."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from pipeline.response import PipelineResponse
from workflow.state import JobState, WorkflowStatus


class JobResult(PlatformModel):
    """Result of a single job execution."""

    job_id: str = Field(min_length=1)
    pipeline_name: str = Field(min_length=1)
    state: JobState
    message: str = Field(min_length=1)
    duration_ms: float = Field(ge=0.0, default=0.0)
    pipeline_response: PipelineResponse | None = None
    started_at: UTCDateTime = Field(default_factory=utc_now)
    completed_at: UTCDateTime | None = None


class WorkflowResult(PlatformModel):
    """Aggregate result of a workflow execution."""

    workflow_id: str = Field(min_length=1)
    status: WorkflowStatus
    completed_jobs: tuple[str, ...] = Field(default_factory=tuple)
    failed_jobs: tuple[str, ...] = Field(default_factory=tuple)
    cancelled_jobs: tuple[str, ...] = Field(default_factory=tuple)
    job_results: tuple[JobResult, ...] = Field(default_factory=tuple)
    metrics: dict[str, Any] = Field(default_factory=dict)
    timings: dict[str, float] = Field(default_factory=dict)
    started_at: UTCDateTime = Field(default_factory=utc_now)
    completed_at: UTCDateTime | None = None
