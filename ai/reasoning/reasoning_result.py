"""Reasoning result contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class ReasoningResult(PlatformModel):
    """Outcome of a reasoning operation."""

    reasoning_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    output: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
