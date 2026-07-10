"""Unit tests for execution orchestrator."""

from __future__ import annotations

import pytest

from core.context.audit_context import AuditContext
from core.context.core_context import CoreContext
from core.context.execution_context import ExecutionContext as CoreExecutionContext
from core.context.identity_context import IdentityContext
from core.context.operation_context import OperationContext
from core.context.request_context import RequestContext
from core.context.security_context import SecurityContext
from execution import ExecutionOrchestrator, ExecutionRegistry, ExecutionState
from execution.exceptions import ExecutionNotFoundError, OrchestrationError
from tests.execution_helpers import (
    FailingExecutionEngine,
    SampleExecutionEngine,
    make_approved_risk_result,
    make_decision_result,
    make_engine_metadata,
    make_rejected_risk_result,
)


def _make_core_context() -> CoreContext:
    return CoreContext(
        trace_id="trace-1",
        correlation_id="corr-1",
        request=RequestContext(request_id="req-1"),
        execution=CoreExecutionContext(execution_id="exec-1"),
        operation=OperationContext(operation_id="op-1", operation_type="execution"),
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
    orchestrator = ExecutionOrchestrator()
    core = _make_core_context()
    decision = make_decision_result()
    risk = make_approved_risk_result()
    context = orchestrator.create_context(
        core_context=core,
        risk_result=risk,
        decision_result=decision,
        input_data={"record_id": "1"},
    )
    assert context.correlation_id == "corr-1"
    assert context.risk_result is not None


def test_orchestrator_execute_success() -> None:
    engines = ExecutionRegistry()
    engines.register(make_engine_metadata())
    engines.register_type(SampleExecutionEngine)
    orchestrator = ExecutionOrchestrator(engine_registry=engines)
    core = _make_core_context()
    context = orchestrator.create_context(
        core_context=core,
        risk_result=make_approved_risk_result(),
        decision_result=make_decision_result(),
    )
    result = orchestrator.execute(context, SampleExecutionEngine())
    assert result.state == ExecutionState.COMPLETED
    assert result.output["prepared"] is True
    assert result.dispatch["success"] is True
    assert engines.get_execution_state(context.execution_id) == ExecutionState.COMPLETED


def test_orchestrator_rejected_risk_fails() -> None:
    engines = ExecutionRegistry()
    engines.register(make_engine_metadata())
    orchestrator = ExecutionOrchestrator(engine_registry=engines)
    context = orchestrator.create_context(
        risk_result=make_rejected_risk_result(),
    )
    result = orchestrator.execute(context, SampleExecutionEngine())
    assert result.state == ExecutionState.FAILED
    assert result.output["reason"] == "validation_failed"


def test_orchestrator_unregistered_engine_raises() -> None:
    orchestrator = ExecutionOrchestrator()
    context = orchestrator.create_context(risk_result=make_approved_risk_result())
    with pytest.raises(ExecutionNotFoundError):
        orchestrator.execute(context, SampleExecutionEngine())


def test_orchestrator_engine_failure_raises() -> None:
    engines = ExecutionRegistry()
    engines.register(make_engine_metadata(engine_id="failing-engine"))
    engines.register_type(FailingExecutionEngine)
    orchestrator = ExecutionOrchestrator(engine_registry=engines)
    context = orchestrator.create_context(
        core_context=_make_core_context(),
        risk_result=make_approved_risk_result(),
    )
    with pytest.raises(OrchestrationError):
        orchestrator.execute(context, FailingExecutionEngine())


def test_orchestrator_cancel() -> None:
    engines = ExecutionRegistry()
    engines.register(make_engine_metadata())
    orchestrator = ExecutionOrchestrator(engine_registry=engines)
    context = orchestrator.create_context(risk_result=make_approved_risk_result())
    engines.track_execution(context.execution_id, engine_id="sample-engine")
    result = orchestrator.cancel(context, "sample-engine")
    assert result.state == ExecutionState.CANCELLED
