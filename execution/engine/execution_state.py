"""Execution lifecycle states."""

from __future__ import annotations

from enum import StrEnum


class ExecutionState(StrEnum):
    """Lifecycle states for execution operations."""

    CREATED = "created"
    VALIDATED = "validated"
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_EXECUTION_STATES: frozenset[ExecutionState] = frozenset(
    {
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
        ExecutionState.CANCELLED,
    },
)
