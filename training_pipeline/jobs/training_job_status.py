"""Training job status definitions."""

from __future__ import annotations

from enum import StrEnum


class TrainingJobStatus(StrEnum):
    """Lifecycle status for a training job."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def is_terminal(self) -> bool:
        return self in {
            TrainingJobStatus.COMPLETED,
            TrainingJobStatus.FAILED,
            TrainingJobStatus.CANCELLED,
        }
