"""Unit tests for adapter metrics."""

from __future__ import annotations

import pytest

from framework_adapters import AdapterMetricsCollector, AdapterState, AdapterSummary, EngineType


@pytest.mark.unit
def test_adapter_metrics_collector_records_state_and_summary() -> None:
    collector = AdapterMetricsCollector()
    collector.record_state(AdapterState.REGISTERED)
    collector.record_summary(
        AdapterSummary(
            adapter_id="adapter-1",
            name="Stub",
            version="1.0.0",
            state=AdapterState.REGISTERED,
            engine_type=EngineType.STUB,
        )
    )
    stats = collector.statistics()
    assert stats.registered_adapters == 1
    assert stats.adapter_validations == 0
    assert stats.adapter_loads == 0
    summary = collector.get_summary("adapter-1")
    assert summary is not None
    assert summary.engine_type == EngineType.STUB
