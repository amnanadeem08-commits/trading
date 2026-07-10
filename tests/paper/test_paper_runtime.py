"""Integration tests for paper adapter runtime."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from connectors import (
    AdapterRegistry,
    ConnectorFrameworkRegistry,
    ConnectorLifecycleManager,
    ConnectorOrchestrator,
    ConnectorRecord,
    PaperExecutionAdapter,
    PaperSettings,
    PaperState,
    reset_adapter_registry,
    reset_connector_framework_registry,
)
from core import CoreRuntime, reset_core_runtime
from events.event_bus import EventBus
from execution import ExecutionOrchestrator, ExecutionRegistry
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context
from tests.connectors_helpers import make_dispatch_request
from tests.execution_helpers import (
    SampleExecutionEngine,
    make_approved_risk_result,
    make_decision_result,
    make_engine_metadata,
)
from tests.paper_helpers import make_paper_adapter_metadata


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_adapter_registry()
    reset_connector_framework_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_adapter_registry()
    reset_connector_framework_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_paper_runtime_full_flow() -> None:
    settings = get_settings()
    assert settings.paper_adapter.enabled is True
    assert settings.connectors.dispatch_bridge_enabled is True

    bus = EventBus()
    application = build_application_context()
    updated_app = ApplicationContext(
        settings=application.settings,
        feature_flags=application.feature_flags,
        event_bus=bus,
        metrics=application.metrics,
        health=application.health,
        audit=application.audit,
        version_registry=application.version_registry,
        logger_factory=application.logger_factory,
        configuration_hash=application.configuration_hash,
    )
    context = build_pipeline_context(updated_app)
    core_runtime = CoreRuntime(context=context)
    core_context = core_runtime.build_context(
        operation_type="paper_pipeline",
        dataset_ids=("records",),
    )
    lifecycle = ConnectorLifecycleManager(event_bus=bus, metrics=updated_app.metrics)

    adapters = AdapterRegistry()
    adapters.register(make_paper_adapter_metadata())
    adapters.register_type(PaperExecutionAdapter)
    connectors = ConnectorFrameworkRegistry(adapter_registry=adapters)
    connectors.register(
        ConnectorRecord(
            connector_id="paper-flow",
            adapter_id="paper-adapter",
            name="Paper",
            version="1.0.0",
        )
    )

    execution_engines = ExecutionRegistry()
    execution_engines.register(make_engine_metadata())
    execution_engines.register_type(SampleExecutionEngine)
    execution_orchestrator = ExecutionOrchestrator(engine_registry=execution_engines)
    execution_context = execution_orchestrator.create_context(
        core_context=core_context,
        risk_result=make_approved_risk_result(),
        decision_result=make_decision_result(),
    )
    execution_result = execution_orchestrator.execute(execution_context, SampleExecutionEngine())
    assert execution_result.state.value == "completed"

    platform_paper = settings.paper_adapter
    paper_adapter = PaperExecutionAdapter(
        settings=PaperSettings(**platform_paper.model_dump()),
    )
    connector_orchestrator = ConnectorOrchestrator(
        connector_registry=connectors,
        adapter_registry=adapters,
        lifecycle=lifecycle,
    )
    request = make_dispatch_request(execution_id=execution_context.execution_id)
    response = connector_orchestrator.dispatch(
        request,
        paper_adapter,
        connector_id="paper-flow",
    )
    connector_orchestrator.shutdown(
        paper_adapter,
        connector_id="paper-flow",
        request=request,
    )

    assert response.success is True
    assert response.output["simulated"] is True
    assert response.output["status"] == PaperState.COMPLETED.value
    assert response.output["validation_passed"] is True
    assert bus.persistence.count() >= 4
    assert len(lifecycle.events) >= 4
    assert core_context.audit.attributes.get("action_recorded") == "paper_pipeline"


@pytest.mark.integration
def test_paper_runtime_dispatch_bridge_response_shape() -> None:
    settings = get_settings()
    adapter = PaperExecutionAdapter(settings=PaperSettings(**settings.paper_adapter.model_dump()))
    adapters = AdapterRegistry()
    adapters.register(make_paper_adapter_metadata())
    adapters.register_type(PaperExecutionAdapter)
    connectors = ConnectorFrameworkRegistry(adapter_registry=adapters)
    connectors.register(
        ConnectorRecord(
            connector_id="paper-bridge",
            adapter_id="paper-adapter",
            name="Paper",
            version="1.0.0",
        )
    )
    orchestrator = ConnectorOrchestrator(connector_registry=connectors, adapter_registry=adapters)
    request = make_dispatch_request()
    response = orchestrator.dispatch(request, adapter, connector_id="paper-bridge")
    assert response.request_id == request.request_id
    assert response.execution_id == request.execution_id
    assert response.adapter_id == "paper-adapter"
    assert "latency_ms" in response.output
    assert "duration_ms" in response.output
    assert "metadata" in response.output
