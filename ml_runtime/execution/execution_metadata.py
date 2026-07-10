"""Execution metadata contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime


class ExecutionMetadata(PlatformModel):
    """Metadata for a runtime execution. No prediction values."""

    execution_id: str
    request_id: str
    model_id: str
    model_version: str
    artifact_reference: str
    executor_id: str
    correlation_id: str
    trace_id: str
    started_at: UTCDateTime
    completed_at: UTCDateTime | None = None
    duration_ms: float = 0.0
    load_time_ms: float = 0.0
    attributes: dict[str, object] = Field(default_factory=dict)
