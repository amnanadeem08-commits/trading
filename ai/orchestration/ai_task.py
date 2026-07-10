"""AI task contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from ai.agents.agent_context import AgentContext
from models.common import PlatformModel, UTCDateTime, utc_now


class AITaskState(StrEnum):
    """Lifecycle states for AI tasks."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AITask(PlatformModel):
    """Registered AI orchestration task."""

    task_id: str = Field(min_length=1)
    agent_id: str = Field(min_length=1)
    prompt_id: str | None = None
    provider_id: str | None = None
    model_id: str | None = None
    state: AITaskState = AITaskState.CREATED
    agent_context: AgentContext | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)
    completed_at: UTCDateTime | None = None
    error_message: str | None = None
