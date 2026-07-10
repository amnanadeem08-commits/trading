"""LLM request contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel


class LLMRequest(PlatformModel):
    """Request contract for LLM provider invocation."""

    request_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    model_name: str = Field(min_length=1, default="default")
    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
