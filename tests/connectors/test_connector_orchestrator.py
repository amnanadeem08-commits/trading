"""Unit tests for connector orchestrator."""

from __future__ import annotations

import pytest

from connectors import (
    AdapterRegistry,
    AdapterState,
    ConnectorFrameworkRegistry,
    ConnectorOrchestrator,
    ConnectorRecord,
)
from connectors.exceptions import AdapterNotFoundError
from tests.connectors_helpers import (
    FailingExecutionAdapter,
    SampleExecutionAdapter,
    make_adapter_metadata,
    make_dispatch_request,
)


def _build_orchestrator() -> ConnectorOrchestrator:
    adapters = AdapterRegistry()
    adapters.register(make_adapter_metadata())
    adapters.register_type(SampleExecutionAdapter)
    connectors = ConnectorFrameworkRegistry(adapter_registry=adapters)
    return ConnectorOrchestrator(
        connector_registry=connectors,
        adapter_registry=adapters,
    )


def test_orchestrator_register_connector() -> None:
    adapters = AdapterRegistry()
    adapters.register(make_adapter_metadata())
    connectors = ConnectorFrameworkRegistry(adapter_registry=adapters)
    orchestrator = ConnectorOrchestrator(connector_registry=connectors, adapter_registry=adapters)
    orchestrator.register_connector(
        connector_id="conn-1",
        adapter_id="sample-adapter",
        name="Sample",
        version="1.0.0",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    assert connectors.exists("conn-1")


def test_orchestrator_dispatch_success() -> None:
    orchestrator = _build_orchestrator()
    adapters = orchestrator._adapters
    connectors = orchestrator._connectors
    connectors.register(
        ConnectorRecord(
            connector_id="conn-1",
            adapter_id="sample-adapter",
            name="Sample",
            version="1.0.0",
        )
    )
    request = make_dispatch_request()
    response = orchestrator.dispatch(
        request,
        SampleExecutionAdapter(),
        connector_id="conn-1",
    )
    assert response.success is True
    assert adapters.get_state("sample-adapter") == AdapterState.ACTIVE


def test_orchestrator_dispatch_unregistered_adapter_raises() -> None:
    orchestrator = _build_orchestrator()
    request = make_dispatch_request()
    with pytest.raises(AdapterNotFoundError):
        orchestrator.dispatch(
            request,
            FailingExecutionAdapter(),
            connector_id="conn-1",
        )


def test_orchestrator_validation_failure() -> None:
    adapters = AdapterRegistry()
    adapters.register(make_adapter_metadata(capabilities=("initialize",)))
    orchestrator = ConnectorOrchestrator(adapter_registry=adapters)
    request = make_dispatch_request()
    response = orchestrator.dispatch(
        request,
        SampleExecutionAdapter(),
        connector_id="conn-1",
        required_capabilities=("dispatch", "missing"),
    )
    assert response.success is False
    assert response.output["reason"] == "validation_failed"


def test_orchestrator_shutdown() -> None:
    orchestrator = _build_orchestrator()
    request = make_dispatch_request()
    orchestrator.shutdown(SampleExecutionAdapter(), connector_id="conn-1", request=request)
    assert orchestrator._adapters.get_state("sample-adapter") == AdapterState.SHUTDOWN


def test_orchestrator_dispatch_failure_returns_unsuccessful_response() -> None:
    adapters = AdapterRegistry()
    adapters.register(make_adapter_metadata(adapter_id="failing-adapter"))
    adapters.register_type(FailingExecutionAdapter)
    orchestrator = ConnectorOrchestrator(adapter_registry=adapters)
    request = make_dispatch_request()
    response = orchestrator.dispatch(
        request,
        FailingExecutionAdapter(),
        connector_id="conn-1",
    )
    assert response.success is False
    assert response.error_message is not None
