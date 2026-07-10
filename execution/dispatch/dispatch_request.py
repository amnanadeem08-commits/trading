"""Dispatch request contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from execution.engine.execution_context import ExecutionContext
from models.common import PlatformModel, UTCDateTime, utc_now


class DispatchRequest(PlatformModel):
    """Request to dispatch a prepared execution contract."""

    request_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    engine_id: str = Field(min_length=1)
    context: ExecutionContext
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    created_at: UTCDateTime = Field(default_factory=utc_now)
