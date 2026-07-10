"""Adapter context contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from execution.engine.execution_context import ExecutionContext
from models.common import PlatformModel


class AdapterContext(PlatformModel):
    """Input context for adapter operations."""

    adapter_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    execution_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    execution_context: ExecutionContext | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
