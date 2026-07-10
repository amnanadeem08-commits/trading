"""Reasoning context contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.agents.agent_context import AgentContext
from models.common import PlatformModel


class ReasoningContext(PlatformModel):
    """Context for a reasoning operation."""

    reasoning_id: str = Field(min_length=1)
    agent_context: AgentContext
    input_data: dict[str, Any] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
