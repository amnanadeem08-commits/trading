"""Approval state definitions."""

from __future__ import annotations

from enum import StrEnum


class ApprovalState(StrEnum):
    """State of a promotion approval workflow."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

    def is_terminal(self) -> bool:
        return self in {
            ApprovalState.APPROVED,
            ApprovalState.REJECTED,
            ApprovalState.CANCELLED,
        }
