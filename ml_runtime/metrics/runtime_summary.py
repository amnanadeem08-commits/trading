"""Runtime summary contracts."""

from __future__ import annotations

from ml_runtime.execution.execution_result import ExecutionStatus
from models.common import PlatformModel


class RuntimeSummary(PlatformModel):
    """Summary for a single runtime execution."""

    execution_id: str
    request_id: str
    model_id: str
    executor_id: str
    status: ExecutionStatus
    runtime_latency_ms: float = 0.0
    load_time_ms: float = 0.0
    execution_time_ms: float = 0.0
    unload_time_ms: float = 0.0
