"""Core operation state."""

from __future__ import annotations

from enum import StrEnum


class OperationState(StrEnum):
    """Lifecycle states for core operations and entities."""

    REGISTERED = "registered"
    INITIALIZED = "initialized"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"


TERMINAL_OPERATION_STATES: frozenset[OperationState] = frozenset(
    {
        OperationState.COMPLETED,
        OperationState.FAILED,
        OperationState.ARCHIVED,
    }
)
