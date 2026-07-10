"""Dispatch result contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class DispatchResult(PlatformModel):
    """Outcome of a dispatch operation."""

    request_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    engine_id: str = Field(min_length=1)
    success: bool = True
    output: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    error_message: str | None = None
    dispatched_at: UTCDateTime = Field(default_factory=utc_now)
