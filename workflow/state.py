"""Workflow and job state definitions."""

from __future__ import annotations

from enum import StrEnum


class JobState(StrEnum):
    """Lifecycle states for a managed job."""

    CREATED = "created"
    QUEUED = "queued"
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    SKIPPED = "skipped"


class WorkflowStatus(StrEnum):
    """Overall workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


TERMINAL_JOB_STATES: frozenset[JobState] = frozenset(
    {
        JobState.COMPLETED,
        JobState.FAILED,
        JobState.CANCELLED,
        JobState.TIMED_OUT,
        JobState.SKIPPED,
    }
)
