"""Dataset operation result models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class DatasetStatus(StrEnum):
    """Overall dataset operation status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    VALIDATED = "validated"


class DatasetResult(PlatformModel):
    """Aggregate result of a dataset operation."""

    dataset_id: str = Field(min_length=1)
    status: DatasetStatus
    record_count: int = Field(ge=0, default=0)
    errors: tuple[str, ...] = Field(default_factory=tuple)
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    metrics: dict[str, Any] = Field(default_factory=dict)
    started_at: UTCDateTime = Field(default_factory=utc_now)
    completed_at: UTCDateTime | None = None
