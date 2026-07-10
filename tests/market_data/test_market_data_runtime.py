"""Integration tests for market data runtime."""

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
from historical import HistoricalRegistry, reset_historical_registry
from market_data import (
    MarketDataRegistry,
    MarketLifecycleEventType,
    MarketLifecycleManager,
    MarketVersionRegistry,
    build_stream_from_repository,
    register_from_repository,
    register_version_from_repository,
    reset_market_data_registry,
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
    reset_market_data_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_adapter_registry()
    reset_connector_framework_registry()
    reset_historical_registry()
    reset_market_data_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_market_data_runtime_full_flow() -> None:
    settings = get_settings()
    assert settings.market_data.validation_enabled is True
    assert settings.market_data.normalization_enabled is True
    assert settings.market_data.stream_buffer_size == 100

    historical = HistoricalRegistry()
    seed_repository(historical.repository)

    market_registry = MarketDataRegistry()
    register_from_repository(
        historical.repository,
        market_registry,
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        name="Sample Market Dataset",
    )
    market_versions = MarketVersionRegistry()
    register_version_from_repository(historical.repository, market_versions, dataset_id="dataset-1")

    stream_buffer = build_stream_from_repository(
        historical.repository,
        dataset_id="dataset-1",
        symbol_id="symbol-1",
        stream_id="market-stream",
        buffer_size=settings.market_data.stream_buffer_size,
        batch_size=settings.market_data.batch_size,
    )

    bus = EventBus()
    metrics = build_application_context().metrics
    lifecycle = MarketLifecycleManager(event_bus=bus, metrics=metrics)
    lifecycle.emit(
        MarketLifecycleEventType.STREAM_STARTED,
        dataset_id="dataset-1",
        correlation_id="corr-market",
        trace_id="trace-market",
        message="stream started",
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
        operation_type="market_data_pipeline",
        dataset_ids=("dataset-1",),
    )

    adapters = AdapterRegistry()
    adapters.register(make_paper_adapter_metadata())
    adapters.register_type(PaperExecutionAdapter)
    connectors = ConnectorFrameworkRegistry(adapter_registry=adapters)
    connectors.register(
        ConnectorRecord(
            connector_id="paper-market-data",
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
        stream_buffer=stream_buffer,
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
        connector_id="paper-market-data",
    )

    assert response.success is True
    assert response.output["simulated"] is True
    assert response.output["metadata"].get("market_data_stream") == "true"
    assert response.output["synthetic_fill"]["close"] == "100.0"
    assert market_registry.exists("dataset-1") is True
    assert market_versions.latest("dataset-1").version == "1.0.0"
    assert len(lifecycle.events) == 1
    assert core_context.audit.attributes.get("action_recorded") == "market_data_pipeline"
