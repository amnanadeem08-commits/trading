"""Execution result contracts."""

from __future__ import annotations

from enum import StrEnum

from ml_runtime.execution.execution_metadata import ExecutionMetadata
from models.common import PlatformModel


class ExecutionStatus(StrEnum):
    """Runtime execution status values."""

    PENDING = "pending"
    LOADING = "loading"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNLOADED = "unloaded"


class ExecutionResult(PlatformModel):
    """Result envelope for runtime execution. Metadata only."""

    execution_id: str
    request_id: str
    status: ExecutionStatus
    metadata: ExecutionMetadata | None = None
    message: str = ""
