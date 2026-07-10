"""Agent context contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from core.context.core_context import CoreContext
from models.common import PlatformModel


class AgentContext(PlatformModel):
    """Context for an agent execution."""

    agent_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    core_context: CoreContext | None = None
    model_id: str | None = None
    prompt_id: str | None = None
    provider_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
