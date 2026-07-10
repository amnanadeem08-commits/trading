"""Pipeline response contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from pipeline.request import PipelineRequest
from pipeline.result import PipelineResult


class PipelineResponse(PlatformModel):
    """Response envelope combining request metadata and pipeline result."""

    request: PipelineRequest
    result: PipelineResult
    completed_at: UTCDateTime = Field(default_factory=utc_now)
