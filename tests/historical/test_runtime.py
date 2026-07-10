"""Integration tests for historical runtime."""

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
    reset_adapter_registry,
    reset_connector_framework_registry,
)
from core import CoreRuntime, reset_core_runtime
from events.event_bus import EventBus
from execution import ExecutionOrchestrator, ExecutionRegistry
from historical import (
    HistoricalLifecycleEventType,
    HistoricalLifecycleManager,
    HistoricalRegistry,
    ReplayContext,
    reset_historical_registry,
)
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context
from tests.connectors_helpers import make_dispatch_request
from tests.execution_helpers import (
    SampleExecutionEngine,
    make_approved_risk_result,
    make_decision_result,
    make_engine_metadata,
)
from tests.historical_helpers import seed_repository
from tests.paper_helpers import make_paper_adapter_metadata


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_adapter_registry()
    reset_connector_framework_registry()
    reset_historical_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_adapter_registry()
    reset_connector_framework_registry()
    reset_historical_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_historical_runtime_full_flow() -> None:
    settings = get_settings()
    assert settings.historical.storage_backend == "in_memory"
    assert settings.historical.replay_enabled is True

    historical = HistoricalRegistry()
    seed_repository(historical.repository)
    historical.replay.begin(
        ReplayContext(dataset_id="dataset-1", version="1.0.0", deterministic=True)
    )

    bus = EventBus()
    metrics = build_application_context().metrics
    historical_lifecycle = HistoricalLifecycleManager(event_bus=bus, metrics=metrics)
    historical_lifecycle.emit(
        HistoricalLifecycleEventType.REPLAY_STARTED,
        dataset_id="dataset-1",
        correlation_id="corr-hist",
        trace_id="trace-hist",
        message="replay started",
    )

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
        operation_type="historical_pipeline",
        dataset_ids=("dataset-1",),
    )

    adapters = AdapterRegistry()
    adapters.register(make_paper_adapter_metadata())
    adapters.register_type(PaperExecutionAdapter)
    connectors = ConnectorFrameworkRegistry(adapter_registry=adapters)
    connectors.register(
        ConnectorRecord(
            connector_id="paper-historical",
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
    execution_orchestrator.execute(execution_context, SampleExecutionEngine())

    paper_adapter = PaperExecutionAdapter(
        settings=PaperSettings(**settings.paper_adapter.model_dump()),
        replay_engine=historical.replay,
    )
    connector_lifecycle = ConnectorLifecycleManager(event_bus=bus, metrics=metrics)
    connector_orchestrator = ConnectorOrchestrator(
        connector_registry=connectors,
        adapter_registry=adapters,
        lifecycle=connector_lifecycle,
    )
    request = make_dispatch_request(execution_id=execution_context.execution_id)
    response = connector_orchestrator.dispatch(
        request,
        paper_adapter,
        connector_id="paper-historical",
    )

    assert response.success is True
    assert response.output["simulated"] is True
    assert response.output["metadata"].get("historical_replay") == "true"
    assert response.output["synthetic_fill"]["value"] == 100.0
    assert len(historical_lifecycle.events) == 1
    assert core_context.audit.attributes.get("action_recorded") == "historical_pipeline"
