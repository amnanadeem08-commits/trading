"""Agent lifecycle states."""

from __future__ import annotations

from enum import StrEnum


class AgentState(StrEnum):
    """Lifecycle states for AI agents."""

    CREATED = "created"
    INITIALIZED = "initialized"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DISABLED = "disabled"


TERMINAL_AGENT_STATES: frozenset[AgentState] = frozenset(
    {
        AgentState.COMPLETED,
        AgentState.FAILED,
        AgentState.DISABLED,
    }
)
