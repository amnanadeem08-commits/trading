"""Inference result contract."""

from __future__ import annotations

from enum import StrEnum

from inference_pipeline.responses.inference_metadata import InferenceMetadata
from models.common import PlatformModel


class InferenceStatus(StrEnum):
    """Lifecycle status for an inference request."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    def is_terminal(self) -> bool:
        return self in {
            InferenceStatus.COMPLETED,
            InferenceStatus.FAILED,
            InferenceStatus.CANCELLED,
        }


class InferenceResult(PlatformModel):
    """Outcome of an inference orchestration run. Metadata only."""

    request_id: str
    status: InferenceStatus
    metadata: InferenceMetadata | None = None
    message: str = ""
