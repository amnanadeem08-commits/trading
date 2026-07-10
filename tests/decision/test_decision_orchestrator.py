"""Unit tests for decision orchestrator."""

from __future__ import annotations

import pytest

from ai.reasoning.reasoning_result import ReasoningResult
from core.context.audit_context import AuditContext
from core.context.core_context import CoreContext
from core.context.execution_context import ExecutionContext
from core.context.identity_context import IdentityContext
from core.context.operation_context import OperationContext
from core.context.request_context import RequestContext
from core.context.security_context import SecurityContext
from decision import (
    DecisionOrchestrator,
    DecisionRegistry,
    DecisionState,
    PolicyRegistry,
)
from decision.exceptions import DecisionNotFoundError, OrchestrationError, PolicyNotFoundError
from ml.inference.prediction_result import PredictionResult
from tests.decision_helpers import (
    FailingDecisionEngine,
    RejectingPolicy,
    SampleDecisionEngine,
    SamplePolicy,
    make_engine_metadata,
    make_policy_metadata,
)


def _make_core_context() -> CoreContext:
    return CoreContext(
        trace_id="trace-1",
        correlation_id="corr-1",
        request=RequestContext(request_id="req-1"),
        execution=ExecutionContext(execution_id="exec-1"),
        operation=OperationContext(operation_id="op-1", operation_type="decision"),
        identity=IdentityContext(),
        security=SecurityContext(),
        audit=AuditContext(
            audit_id="audit-1",
            action="test",
            resource_type="entity",
            resource_id="sample-entity",
        ),
        dataset_ids=("records",),
    )


def test_orchestrator_create_context() -> None:
    orchestrator = DecisionOrchestrator()
    core = _make_core_context()
    context = orchestrator.create_context(
        core_context=core,
        input_data={"record_id": "1"},
    )
    assert context.correlation_id == "corr-1"
    assert context.trace_id == "trace-1"
    assert context.input_data["record_id"] == "1"


def test_orchestrator_decide_success() -> None:
    engines = DecisionRegistry()
    policies = PolicyRegistry()
    engines.register(make_engine_metadata())
    engines.register_type(SampleDecisionEngine)
    policies.register(make_policy_metadata())
    policies.register_type(SamplePolicy)

    orchestrator = DecisionOrchestrator(
        engine_registry=engines,
        policy_registry=policies,
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
    context = orchestrator.create_context(ai_result=ai_result, ml_result=ml_result)
    result = orchestrator.decide(context, SampleDecisionEngine(), policy_id="sample-policy")
    assert result.state == DecisionState.COMPLETED
    assert result.confidence >= 0.85
    assert result.evaluation["quality_score"] >= 0.0
    assert engines.get_state("sample-engine") == DecisionState.COMPLETED


def test_orchestrator_decide_rejected() -> None:
    engines = DecisionRegistry()
    policies = PolicyRegistry()
    engines.register(make_engine_metadata())
    engines.register_type(SampleDecisionEngine)
    policies.register(make_policy_metadata(policy_id="rejecting-policy"))
    policies.register_type(RejectingPolicy)

    orchestrator = DecisionOrchestrator(engine_registry=engines, policy_registry=policies)
    context = orchestrator.create_context()
    result = orchestrator.decide(
        context,
        SampleDecisionEngine(),
        policy_id="rejecting-policy",
        policy=RejectingPolicy(),
    )
    assert result.state == DecisionState.REJECTED
    assert engines.get_state("sample-engine") == DecisionState.REJECTED


def test_orchestrator_engine_not_found() -> None:
    orchestrator = DecisionOrchestrator()
    context = orchestrator.create_context()
    with pytest.raises(DecisionNotFoundError):
        orchestrator.decide(context, SampleDecisionEngine(), policy_id="sample-policy")


def test_orchestrator_policy_not_found() -> None:
    engines = DecisionRegistry()
    engines.register(make_engine_metadata())
    orchestrator = DecisionOrchestrator(engine_registry=engines)
    context = orchestrator.create_context()
    with pytest.raises(PolicyNotFoundError):
        orchestrator.decide(context, SampleDecisionEngine(), policy_id="missing")


def test_orchestrator_failure() -> None:
    engines = DecisionRegistry()
    policies = PolicyRegistry()
    engines.register(make_engine_metadata(engine_id="failing-engine"))
    engines.register_type(FailingDecisionEngine)
    policies.register(make_policy_metadata())
    policies.register_type(SamplePolicy)

    orchestrator = DecisionOrchestrator(engine_registry=engines, policy_registry=policies)
    context = orchestrator.create_context()
    with pytest.raises(OrchestrationError):
        orchestrator.decide(context, FailingDecisionEngine(), policy_id="sample-policy")
    assert engines.get_state("failing-engine") == DecisionState.FAILED
