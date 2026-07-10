"""Integration tests for execution layer runtime."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from core import CoreRuntime, reset_core_runtime
from events.event_bus import EventBus
from execution import (
    ExecutionLifecycleManager,
    ExecutionOrchestrator,
    ExecutionRegistry,
    ExecutionState,
    get_execution_registry,
    reset_execution_registry,
)
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context
from tests.execution_helpers import (
    SampleExecutionEngine,
    make_approved_risk_result,
    make_decision_result,
    make_engine_metadata,
)


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_execution_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_execution_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_execution_runtime_full_orchestration_flow() -> None:
    settings = get_settings()
    assert settings.execution.registry_enabled is True
    assert settings.execution.lifecycle_enabled is True
    assert settings.execution.dispatch_enabled is True

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
        operation_type="execution_pipeline",
        dataset_ids=("records",),
    )
    lifecycle = ExecutionLifecycleManager(context)

    engines = ExecutionRegistry()
    engines.register(make_engine_metadata())
    engines.register_type(SampleExecutionEngine)
    orchestrator = ExecutionOrchestrator(
        engine_registry=engines,
        lifecycle=lifecycle,
    )

    decision_result = make_decision_result()
    risk_result = make_approved_risk_result()
    execution_context = orchestrator.create_context(
        core_context=core_context,
        risk_result=risk_result,
        decision_result=decision_result,
        input_data={"record_id": "1"},
    )
    result = orchestrator.execute(execution_context, SampleExecutionEngine())

    assert result.state == ExecutionState.COMPLETED
    assert result.output["prepared"] is True
    assert result.dispatch["success"] is True
    assert bus.persistence.count() >= 5
    assert len(lifecycle.events) >= 5
    assert core_context.audit.attributes.get("action_recorded") == "execution_pipeline"


@pytest.mark.integration
def test_execution_runtime_singleton_registry() -> None:
    registry = get_execution_registry()
    registry.register(make_engine_metadata(engine_id="singleton"))
    assert get_execution_registry().list() == ("singleton",)
