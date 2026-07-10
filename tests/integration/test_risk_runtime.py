"""Integration tests for risk layer runtime."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from core import CoreRuntime, reset_core_runtime
from decision.engine.decision_result import DecisionResult
from decision.engine.decision_state import DecisionState
from events.event_bus import EventBus
from pipeline import build_pipeline_context
from risk import (
    PolicyRegistry,
    RiskLifecycleEventType,
    RiskLifecycleManager,
    RiskOrchestrator,
    RiskRegistry,
    RiskState,
    Validator,
    get_risk_registry,
    reset_policy_registry,
    reset_risk_registry,
)
from services import ApplicationContext, build_application_context, reset_application_context
from tests.risk_helpers import (
    PassingRule,
    SamplePolicy,
    SampleRiskEngine,
    make_engine_metadata,
    make_policy_metadata,
)


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_risk_registry()
    reset_policy_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_risk_registry()
    reset_policy_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_risk_runtime_full_orchestration_flow() -> None:
    settings = get_settings()
    assert settings.risk.registry_enabled is True
    assert settings.risk.lifecycle_enabled is True

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
        operation_type="risk_pipeline",
        dataset_ids=("records",),
    )
    lifecycle = RiskLifecycleManager(context)

    engines = RiskRegistry()
    policies = PolicyRegistry()
    engines.register(make_engine_metadata())
    engines.register_type(SampleRiskEngine)
    policies.register(make_policy_metadata())
    policies.register_type(SamplePolicy)
    validator = Validator((PassingRule(),))

    orchestrator = RiskOrchestrator(
        engine_registry=engines,
        policy_registry=policies,
        validator=validator,
    )
    lifecycle.emit(
        RiskLifecycleEventType.RISK_STARTED,
        risk_id="risk-flow",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="starting",
    )

    decision_result = DecisionResult(
        decision_id="dec-1",
        engine_id="decision-engine",
        state=DecisionState.COMPLETED,
        output={"outcome": "approved"},
        confidence=0.9,
    )
    risk_context = orchestrator.create_context(
        core_context=core_context,
        decision_result=decision_result,
        input_data={"record_id": "1"},
    )
    result = orchestrator.assess(
        risk_context,
        SampleRiskEngine(),
        policy_id="sample-policy",
    )

    lifecycle.emit(
        RiskLifecycleEventType.RISK_VALIDATED,
        risk_id=risk_context.risk_id,
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="validated",
    )
    lifecycle.emit(
        RiskLifecycleEventType.RISK_APPROVED,
        risk_id=risk_context.risk_id,
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="approved",
    )
    lifecycle.emit(
        RiskLifecycleEventType.RISK_COMPLETED,
        risk_id=risk_context.risk_id,
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="completed",
    )

    assert result.state == RiskState.APPROVED
    assert result.approval is not None
    assert result.approval.approved is True
    assert bus.persistence.count() >= 4
    assert len(lifecycle.events) >= 4


@pytest.mark.integration
def test_risk_runtime_singleton_registry() -> None:
    registry = get_risk_registry()
    registry.register(make_engine_metadata(engine_id="singleton"))
    assert get_risk_registry().list() == ("singleton",)
