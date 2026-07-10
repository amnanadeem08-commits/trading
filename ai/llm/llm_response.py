"""LLM response contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class LLMResponse(PlatformModel):
    """Response contract from an LLM provider."""

    request_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    content: str = ""
    model_name: str = Field(min_length=1, default="default")
    token_count: int = Field(ge=0, default=0)
    metadata: dict[str, str] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
