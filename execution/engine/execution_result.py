"""Execution result contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from execution.engine.execution_state import ExecutionState
from models.common import PlatformModel, UTCDateTime, utc_now


class ExecutionResult(PlatformModel):
    """Outcome of an execution operation."""

    execution_id: str = Field(min_length=1)
    engine_id: str = Field(min_length=1)
    state: ExecutionState = ExecutionState.COMPLETED
    output: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    dispatch: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    version_info: dict[str, str] = Field(default_factory=dict)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
