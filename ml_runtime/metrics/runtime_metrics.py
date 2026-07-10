"""Runtime metrics collection."""

from __future__ import annotations

from threading import RLock

from ml_runtime.execution.execution_result import ExecutionStatus
from ml_runtime.metrics.runtime_statistics import RuntimeStatistics
from ml_runtime.metrics.runtime_summary import RuntimeSummary


class RuntimeMetricsCollector:
    """Collects ML runtime metrics without external backends."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._status_counts: dict[ExecutionStatus, int] = {status: 0 for status in ExecutionStatus}
        self._total_runtime_latency_ms = 0.0
        self._total_load_time_ms = 0.0
        self._total_execution_time_ms = 0.0
        self._total_unload_time_ms = 0.0
        self._summaries: dict[str, RuntimeSummary] = {}

    def record_status(self, status: ExecutionStatus) -> None:
        with self._lock:
            self._status_counts[status] = self._status_counts.get(status, 0) + 1

    def record_timing(
        self,
        *,
        runtime_latency_ms: float = 0.0,
        load_time_ms: float = 0.0,
        execution_time_ms: float = 0.0,
        unload_time_ms: float = 0.0,
    ) -> None:
        with self._lock:
            self._total_runtime_latency_ms += runtime_latency_ms
            self._total_load_time_ms += load_time_ms
            self._total_execution_time_ms += execution_time_ms
            self._total_unload_time_ms += unload_time_ms

    def record_summary(self, summary: RuntimeSummary) -> None:
        with self._lock:
            self._summaries[summary.execution_id] = summary

    def statistics(self) -> RuntimeStatistics:
        with self._lock:
            total = sum(self._status_counts.values())
            completed = self._status_counts.get(ExecutionStatus.COMPLETED, 0)
            throughput = (completed / max(total, 1)) * 60.0
            return RuntimeStatistics(
                total_executions=total,
                completed_executions=completed,
                failed_executions=self._status_counts.get(ExecutionStatus.FAILED, 0),
                total_runtime_latency_ms=self._total_runtime_latency_ms,
                total_load_time_ms=self._total_load_time_ms,
                total_execution_time_ms=self._total_execution_time_ms,
                total_unload_time_ms=self._total_unload_time_ms,
                throughput_per_minute=throughput,
            )

    def get_summary(self, execution_id: str) -> RuntimeSummary | None:
        with self._lock:
            return self._summaries.get(execution_id)
