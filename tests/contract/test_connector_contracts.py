"""Contract tests for connector framework."""

from __future__ import annotations

import inspect

import pytest

from connectors import (
    AdapterRegistry,
    ConnectorDispatchRequest,
    ConnectorFrameworkRegistry,
    ConnectorOrchestrator,
    ConnectorValidator,
    ConnectorVersion,
    DispatchBridge,
    DispatchResponse,
    ExecutionAdapter,
)
from tests.connectors_helpers import SampleExecutionAdapter, make_dispatch_request


@pytest.mark.contract
def test_execution_adapter_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ExecutionAdapter, predicate=inspect.isfunction)
    }
    assert "initialize" in methods
    assert "dispatch" in methods
    assert "health" in methods


@pytest.mark.contract
def test_sample_adapter_compliance() -> None:
    adapter = SampleExecutionAdapter()
    assert adapter.adapter_id() == "sample-adapter"
    health = adapter.health()
    assert health.adapter_id == "sample-adapter"


@pytest.mark.contract
def test_dispatch_response_fields() -> None:
    response = DispatchResponse(
        request_id="req-1",
        execution_id="exec-1",
        adapter_id="sample-adapter",
    )
    assert response.success is True


@pytest.mark.contract
def test_bridge_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(DispatchBridge, predicate=inspect.isfunction)}
    assert "route" in methods
    assert "wrap_request" in methods


@pytest.mark.contract
def test_adapter_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(AdapterRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "resolve" in methods


@pytest.mark.contract
def test_connector_framework_registry_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(ConnectorFrameworkRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "resolve" in methods


@pytest.mark.contract
def test_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ConnectorValidator, predicate=inspect.isfunction)
    }
    assert "validate" in methods


@pytest.mark.contract
def test_orchestrator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ConnectorOrchestrator, predicate=inspect.isfunction)
    }
    assert "dispatch" in methods
    assert "shutdown" in methods


@pytest.mark.contract
def test_version_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ConnectorVersion, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "is_compatible" in methods


@pytest.mark.contract
def test_connector_dispatch_request_wraps_execution_request() -> None:
    request = make_dispatch_request()
    bridge = DispatchBridge()
    wrapped = bridge.wrap_request(request, adapter_id="sample-adapter")
    assert isinstance(wrapped, ConnectorDispatchRequest)
    assert wrapped.request.execution_id == "exec-1"
