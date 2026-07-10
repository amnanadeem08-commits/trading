"""Paper execution lifecycle states."""

from __future__ import annotations

from enum import StrEnum


class PaperState(StrEnum):
    """Lifecycle states for paper execution records."""

    NEW = "new"
    QUEUED = "queued"
    ACCEPTED = "accepted"
    SIMULATED = "simulated"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_PAPER_STATES: frozenset[PaperState] = frozenset(
    {
        PaperState.COMPLETED,
        PaperState.FAILED,
        PaperState.CANCELLED,
    },
)
