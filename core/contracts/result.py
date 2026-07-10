"""Core result contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class ResultStatus(StrEnum):
    """Outcome status for core operations."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class OperationResult(PlatformModel):
    """Generic result contract for core operations."""

    operation_id: str = Field(min_length=1)
    status: ResultStatus
    entity_id: str | None = None
    message: str = ""
    payload: dict[str, Any] = Field(default_factory=dict)
    errors: tuple[str, ...] = Field(default_factory=tuple)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
