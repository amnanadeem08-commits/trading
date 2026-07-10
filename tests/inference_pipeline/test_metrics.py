"""Unit tests for inference metrics."""

from __future__ import annotations

import pytest

from inference_pipeline import InferenceMetricsCollector, InferenceStatus, InferenceSummary


@pytest.mark.unit
def test_metrics_collector_statistics() -> None:
    collector = InferenceMetricsCollector()
    collector.record_status(InferenceStatus.QUEUED)
    collector.record_status(InferenceStatus.COMPLETED)
    collector.record_latency(10.0, queue_time_ms=2.0)
    stats = collector.statistics()
    assert stats.total_requests == 2
    assert stats.completed_requests == 1
    assert stats.total_latency_ms == 10.0


@pytest.mark.unit
def test_metrics_collector_summary() -> None:
    collector = InferenceMetricsCollector()
    collector.record_summary(
        InferenceSummary(
            request_id="req-1",
            model_id="model-1",
            status=InferenceStatus.COMPLETED,
            latency_ms=5.0,
        )
    )
    assert collector.get_summary("req-1") is not None
