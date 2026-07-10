"""Decision lifecycle states."""

from __future__ import annotations

from enum import StrEnum


class DecisionState(StrEnum):
    """Lifecycle states for decision operations."""

    CREATED = "created"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


TERMINAL_DECISION_STATES: frozenset[DecisionState] = frozenset(
    {
        DecisionState.COMPLETED,
        DecisionState.REJECTED,
        DecisionState.FAILED,
    },
)
