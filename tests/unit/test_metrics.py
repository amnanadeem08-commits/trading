"""Unit tests for metrics scaffolds."""

from __future__ import annotations

import pytest

from metrics import MetricRegistry
from models.common import ContractViolationError


@pytest.mark.unit
def test_metric_registry_counter_gauge_histogram_timer() -> None:
    registry = MetricRegistry()
    registry.counter("requests_total").inc(2)
    registry.gauge("active_connections").set(5)
    registry.histogram("latency").observe(0.5)
    with registry.timer("operation").start():
        pass
    snapshot = registry.snapshot()
    assert snapshot["counter:requests_total"] == 2.0
    assert snapshot["gauge:active_connections"] == 5.0
    assert snapshot["histogram:latency:count"] == 1
    assert snapshot["histogram:operation_duration:count"] == 1


@pytest.mark.unit
def test_metric_registry_list_metrics() -> None:
    registry = MetricRegistry()
    registry.counter("a")
    registry.gauge("b")
    listed = registry.list_metrics()
    assert listed["counters"] == ("a",)
    assert listed["gauges"] == ("b",)


@pytest.mark.unit
def test_metric_registry_missing_counter_raises() -> None:
    registry = MetricRegistry()
    with pytest.raises(ContractViolationError):
        registry.get_counter("missing")
