"""Unit tests for runtime metrics."""

from __future__ import annotations

import pytest

from ml_runtime import ExecutionStatus, RuntimeMetricsCollector, RuntimeSummary


@pytest.mark.unit
def test_metrics_collector_records_statistics() -> None:
    collector = RuntimeMetricsCollector()
    collector.record_status(ExecutionStatus.COMPLETED)
    collector.record_timing(
        runtime_latency_ms=10.0,
        load_time_ms=2.0,
        execution_time_ms=5.0,
        unload_time_ms=1.0,
    )
    collector.record_summary(
        RuntimeSummary(
            execution_id="exec-1",
            request_id="req-1",
            model_id="model-1",
            executor_id="executor-1",
            status=ExecutionStatus.COMPLETED,
            runtime_latency_ms=10.0,
        )
    )
    stats = collector.statistics()
    assert stats.completed_executions == 1
    assert stats.total_runtime_latency_ms == 10.0
    assert collector.get_summary("exec-1") is not None
