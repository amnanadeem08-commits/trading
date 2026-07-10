"""Unit tests for paper adapter orchestration."""

from __future__ import annotations

from connectors import (
    AdapterRegistry,
    ConnectorFrameworkRegistry,
    ConnectorOrchestrator,
    ConnectorRecord,
    PaperExecutionAdapter,
    PaperState,
)
from tests.connectors_helpers import make_dispatch_request
from tests.paper_helpers import make_paper_adapter, make_paper_adapter_metadata


def _build_orchestrator() -> ConnectorOrchestrator:
    adapters = AdapterRegistry()
    adapters.register(make_paper_adapter_metadata())
    adapters.register_type(PaperExecutionAdapter)
    connectors = ConnectorFrameworkRegistry(adapter_registry=adapters)
    return ConnectorOrchestrator(
        connector_registry=connectors,
        adapter_registry=adapters,
    )


def test_paper_orchestrator_dispatch_success() -> None:
    orchestrator = _build_orchestrator()
    connectors = orchestrator._connectors
    connectors.register(
        ConnectorRecord(
            connector_id="paper-conn",
            adapter_id="paper-adapter",
            name="Paper",
            version="1.0.0",
        )
    )
    request = make_dispatch_request()
    response = orchestrator.dispatch(
        request,
        make_paper_adapter(),
        connector_id="paper-conn",
    )
    assert response.success is True
    assert response.output["simulated"] is True
    assert response.output["status"] == PaperState.COMPLETED.value


def test_paper_orchestrator_shutdown() -> None:
    orchestrator = _build_orchestrator()
    adapter = make_paper_adapter()
    request = make_dispatch_request()
    orchestrator.dispatch(adapter=adapter, request=request, connector_id="paper-conn")
    orchestrator.shutdown(adapter, connector_id="paper-conn", request=request)
    assert adapter.state == PaperState.CANCELLED


def test_paper_orchestrator_register_connector() -> None:
    orchestrator = _build_orchestrator()
    orchestrator.register_connector(
        connector_id="paper-conn",
        adapter_id="paper-adapter",
        name="Paper",
        version="1.0.0",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    assert orchestrator._connectors.exists("paper-conn")
