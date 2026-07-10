"""Risk lifecycle states."""

from __future__ import annotations

from enum import StrEnum


class RiskState(StrEnum):
    """Lifecycle states for risk operations."""

    CREATED = "created"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


TERMINAL_RISK_STATES: frozenset[RiskState] = frozenset(
    {
        RiskState.APPROVED,
        RiskState.REJECTED,
        RiskState.FAILED,
    },
)
