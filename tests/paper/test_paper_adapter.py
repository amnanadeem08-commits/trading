"""Unit tests for paper execution adapter."""

from __future__ import annotations

import inspect

import pytest

from connectors import ExecutionAdapter, PaperState
from connectors.adapters.adapter_metadata import AdapterHealthStatus
from connectors.adapters.adapter_registry import AdapterRegistry
from connectors.dispatch.dispatch_bridge import DispatchBridge
from connectors.exceptions import DispatchBridgeError
from tests.connectors_helpers import make_dispatch_request
from tests.paper_helpers import (
    make_paper_adapter,
    make_paper_adapter_context,
    make_paper_adapter_metadata,
    make_paper_settings,
)


def test_paper_adapter_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ExecutionAdapter, predicate=inspect.isfunction)
    }
    assert "initialize" in methods
    assert "validate" in methods
    assert "dispatch" in methods
    assert "shutdown" in methods
    assert "health" in methods


def test_paper_adapter_metadata() -> None:
    adapter = make_paper_adapter()
    metadata = adapter.metadata()
    assert metadata.adapter_id == "paper-adapter"
    assert "dispatch" in metadata.capabilities
    assert "simulate" in metadata.capabilities


def test_paper_adapter_lifecycle() -> None:
    adapter = make_paper_adapter()
    context = make_paper_adapter_context()
    adapter.initialize(context)
    assert adapter.state == PaperState.ACCEPTED
    assert adapter.validate(context) is True
    output = adapter.dispatch(context)
    assert output["simulated"] is True
    assert output["status"] == PaperState.COMPLETED.value
    assert adapter.state == PaperState.COMPLETED
    adapter.shutdown(context)
    assert adapter.state == PaperState.CANCELLED


def test_paper_adapter_record_tracking() -> None:
    adapter = make_paper_adapter()
    context = make_paper_adapter_context()
    adapter.initialize(context)
    record = adapter.get_record(context.request_id)
    assert record is not None
    assert record.state == PaperState.ACCEPTED
    adapter.dispatch(context)
    updated = adapter.get_record(context.request_id)
    assert updated is not None
    assert updated.state == PaperState.COMPLETED


def test_paper_adapter_health_disabled() -> None:
    adapter = make_paper_adapter(settings=make_paper_settings(enabled=False))
    health = adapter.health()
    assert health.status == AdapterHealthStatus.DEGRADED


def test_paper_adapter_health_failed_state() -> None:
    adapter = make_paper_adapter(settings=make_paper_settings(failure_rate=1.0))
    context = make_paper_adapter_context()
    adapter.initialize(context)
    adapter.dispatch(context)
    assert adapter.state == PaperState.FAILED
    health = adapter.health()
    assert health.status == AdapterHealthStatus.UNHEALTHY


def test_paper_adapter_validation_rejects_disabled() -> None:
    adapter = make_paper_adapter(settings=make_paper_settings(enabled=False))
    context = make_paper_adapter_context()
    adapter.initialize(context)
    assert adapter.validate(context) is False


def test_paper_adapter_dispatch_via_bridge() -> None:
    adapters = AdapterRegistry()
    adapters.register(make_paper_adapter_metadata())
    adapter = make_paper_adapter()
    bridge = DispatchBridge(adapter_registry=adapters)
    request = make_dispatch_request()
    connector_request = bridge.wrap_request(request, adapter_id="paper-adapter")
    response = bridge.route(connector_request, adapter)
    assert response.success is True
    assert response.output["simulated"] is True


def test_paper_adapter_bridge_validation_failure() -> None:
    adapters = AdapterRegistry()
    adapters.register(make_paper_adapter_metadata())
    adapter = make_paper_adapter(settings=make_paper_settings(enabled=False))
    bridge = DispatchBridge(adapter_registry=adapters)
    request = make_dispatch_request()
    connector_request = bridge.wrap_request(request, adapter_id="paper-adapter")
    with pytest.raises(DispatchBridgeError, match="validation failed"):
        bridge.route(connector_request, adapter)


def test_paper_adapter_deterministic_output() -> None:
    settings = make_paper_settings(
        deterministic=True, random_seed=7, latency_ms_min=5, latency_ms_max=5
    )
    first = make_paper_adapter(settings=settings)
    second = make_paper_adapter(settings=settings)
    context = make_paper_adapter_context()
    first.initialize(context)
    second.initialize(context)
    first_output = first.dispatch(context)
    second_output = second.dispatch(context)
    assert first_output["latency_ms"] == second_output["latency_ms"]
    assert first_output["duration_ms"] == second_output["duration_ms"]
