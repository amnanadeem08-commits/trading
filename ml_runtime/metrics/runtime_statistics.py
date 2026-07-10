"""Runtime statistics contracts."""

from __future__ import annotations

from models.common import PlatformModel


class RuntimeStatistics(PlatformModel):
    """Aggregate ML runtime statistics."""

    total_executions: int = 0
    completed_executions: int = 0
    failed_executions: int = 0
    total_runtime_latency_ms: float = 0.0
    total_load_time_ms: float = 0.0
    total_execution_time_ms: float = 0.0
    total_unload_time_ms: float = 0.0
    throughput_per_minute: float = 0.0
