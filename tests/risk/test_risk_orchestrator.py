"""Unit tests for risk orchestrator."""

from __future__ import annotations

import pytest

from core.context.audit_context import AuditContext
from core.context.core_context import CoreContext
from core.context.execution_context import ExecutionContext
from core.context.identity_context import IdentityContext
from core.context.operation_context import OperationContext
from core.context.request_context import RequestContext
from core.context.security_context import SecurityContext
from risk import PolicyRegistry, RiskOrchestrator, RiskRegistry, RiskState
from risk.exceptions import OrchestrationError, PolicyNotFoundError, RiskNotFoundError
from risk.validation.validator import Validator
from tests.risk_helpers import (
    FailingRiskEngine,
    FailingRule,
    PassingRule,
    RejectingPolicy,
    SamplePolicy,
    SampleRiskEngine,
    make_decision_result,
    make_engine_metadata,
    make_policy_metadata,
)


def _make_core_context() -> CoreContext:
    return CoreContext(
        trace_id="trace-1",
        correlation_id="corr-1",
        request=RequestContext(request_id="req-1"),
        execution=ExecutionContext(execution_id="exec-1"),
        operation=OperationContext(operation_id="op-1", operation_type="risk"),
        identity=IdentityContext(),
        security=SecurityContext(),
        audit=AuditContext(
            audit_id="audit-1",
            action="test",
            resource_type="entity",
            resource_id="sample-entity",
        ),
    )


def test_orchestrator_create_context() -> None:
    orchestrator = RiskOrchestrator()
    core = _make_core_context()
    decision = make_decision_result()
    context = orchestrator.create_context(
        core_context=core,
        decision_result=decision,
        input_data={"record_id": "1"},
    )
    assert context.correlation_id == "corr-1"
    assert context.decision_result is not None


def test_orchestrator_assess_success() -> None:
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
    context = orchestrator.create_context(decision_result=make_decision_result())
    result = orchestrator.assess(context, SampleRiskEngine(), policy_id="sample-policy")
    assert result.state == RiskState.APPROVED
    assert result.approval is not None
    assert result.approval.approved is True
    assert engines.get_state("sample-engine") == RiskState.APPROVED


def test_orchestrator_validation_failure() -> None:
    engines = RiskRegistry()
    policies = PolicyRegistry()
    engines.register(make_engine_metadata())
    engines.register_type(SampleRiskEngine)
    policies.register(make_policy_metadata())
    validator = Validator((FailingRule(),))

    orchestrator = RiskOrchestrator(
        engine_registry=engines,
        policy_registry=policies,
        validator=validator,
    )
    context = orchestrator.create_context()
    result = orchestrator.assess(context, SampleRiskEngine(), policy_id="sample-policy")
    assert result.state == RiskState.REJECTED
    assert engines.get_state("sample-engine") == RiskState.REJECTED


def test_orchestrator_policy_rejection() -> None:
    engines = RiskRegistry()
    policies = PolicyRegistry()
    engines.register(make_engine_metadata())
    engines.register_type(SampleRiskEngine)
    policies.register(make_policy_metadata(policy_id="rejecting-policy"))
    policies.register_type(RejectingPolicy)
    validator = Validator((PassingRule(),))

    orchestrator = RiskOrchestrator(
        engine_registry=engines,
        policy_registry=policies,
        validator=validator,
    )
    context = orchestrator.create_context()
    result = orchestrator.assess(
        context,
        SampleRiskEngine(),
        policy_id="rejecting-policy",
        policy=RejectingPolicy(),
    )
    assert result.state == RiskState.REJECTED


def test_orchestrator_engine_not_found() -> None:
    orchestrator = RiskOrchestrator(validator=Validator((PassingRule(),)))
    context = orchestrator.create_context()
    with pytest.raises(RiskNotFoundError):
        orchestrator.assess(context, SampleRiskEngine(), policy_id="sample-policy")


def test_orchestrator_policy_not_found() -> None:
    engines = RiskRegistry()
    engines.register(make_engine_metadata())
    orchestrator = RiskOrchestrator(engine_registry=engines, validator=Validator((PassingRule(),)))
    context = orchestrator.create_context()
    with pytest.raises(PolicyNotFoundError):
        orchestrator.assess(context, SampleRiskEngine(), policy_id="missing")


def test_orchestrator_failure() -> None:
    engines = RiskRegistry()
    policies = PolicyRegistry()
    engines.register(make_engine_metadata(engine_id="failing-engine"))
    engines.register_type(FailingRiskEngine)
    policies.register(make_policy_metadata())
    policies.register_type(SamplePolicy)
    validator = Validator((PassingRule(),))

    orchestrator = RiskOrchestrator(
        engine_registry=engines,
        policy_registry=policies,
        validator=validator,
    )
    context = orchestrator.create_context()
    with pytest.raises(OrchestrationError):
        orchestrator.assess(context, FailingRiskEngine(), policy_id="sample-policy")
    assert engines.get_state("failing-engine") == RiskState.FAILED
