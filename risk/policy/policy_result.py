"""Policy evaluation result contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel


class PolicyResult(PlatformModel):
    """Outcome of a risk policy evaluation."""

    policy_id: str = Field(min_length=1)
    compliant: bool = True
    output: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    score: float = Field(ge=0.0, le=1.0, default=0.0)
    version: str = Field(min_length=1, default="1.0.0")
