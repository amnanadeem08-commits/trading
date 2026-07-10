"""Integration tests for decision layer runtime."""

from __future__ import annotations

import pytest

from ai.reasoning.reasoning_result import ReasoningResult
from config.settings import get_settings, reset_settings
from core import CoreRuntime, reset_core_runtime
from decision import (
    DecisionLifecycleEventType,
    DecisionLifecycleManager,
    DecisionOrchestrator,
    DecisionRegistry,
    DecisionState,
    PolicyRegistry,
    get_decision_registry,
    reset_decision_registry,
    reset_policy_registry,
)
from events.event_bus import EventBus
from ml.inference.prediction_result import PredictionResult
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context
from tests.decision_helpers import (
    SampleDecisionEngine,
    SamplePolicy,
    make_engine_metadata,
    make_policy_metadata,
)


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_decision_registry()
    reset_policy_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_decision_registry()
    reset_policy_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_decision_runtime_full_orchestration_flow() -> None:
    settings = get_settings()
    assert settings.decision.registry_enabled is True
    assert settings.decision.lifecycle_enabled is True

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
        operation_type="decision_pipeline",
        dataset_ids=("records",),
    )
    lifecycle = DecisionLifecycleManager(context)

    engines = DecisionRegistry()
    policies = PolicyRegistry()
    engines.register(make_engine_metadata())
    engines.register_type(SampleDecisionEngine)
    policies.register(make_policy_metadata())
    policies.register_type(SamplePolicy)

    orchestrator = DecisionOrchestrator(engine_registry=engines, policy_registry=policies)
    lifecycle.emit(
        DecisionLifecycleEventType.DECISION_STARTED,
        decision_id="dec-flow",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="starting",
    )

    ai_result = ReasoningResult(
        reasoning_id="reason-1",
        agent_id="agent-1",
        output={"score": 0.9},
        confidence=0.9,
    )
    ml_result = PredictionResult(
        inference_id="inf-1",
        model_id="model-1",
        model_version="1.0.0",
        outputs=({"value": 0.8},),
    )
    decision_context = orchestrator.create_context(
        core_context=core_context,
        ai_result=ai_result,
        ml_result=ml_result,
        input_data={"record_id": "1"},
    )
    result = orchestrator.decide(
        decision_context,
        SampleDecisionEngine(),
        policy_id="sample-policy",
    )

    lifecycle.emit(
        DecisionLifecycleEventType.DECISION_COMPLETED,
        decision_id=decision_context.decision_id,
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="completed",
        payload={"engine_id": result.engine_id},
    )

    assert result.state == DecisionState.COMPLETED
    assert result.confidence >= 0.85
    assert result.evaluation["quality_score"] >= 0.0
    assert bus.persistence.count() >= 2
    assert len(lifecycle.events) >= 2


@pytest.mark.integration
def test_decision_runtime_singleton_registry() -> None:
    registry = get_decision_registry()
    registry.register(make_engine_metadata(engine_id="singleton"))
    assert get_decision_registry().list() == ("singleton",)
