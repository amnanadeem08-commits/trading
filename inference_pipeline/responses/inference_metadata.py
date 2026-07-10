"""Inference metadata contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime


class InferenceMetadata(PlatformModel):
    """Metadata describing an inference orchestration run."""

    request_id: str
    model_id: str
    version_id: str
    artifact_id: str
    config_hash: str
    checksum: str
    stage: str
    correlation_id: str
    trace_id: str
    started_at: UTCDateTime
    completed_at: UTCDateTime | None = None
    duration_ms: float = 0.0
    queue_time_ms: float = 0.0
    attributes: dict[str, object] = Field(default_factory=dict)
