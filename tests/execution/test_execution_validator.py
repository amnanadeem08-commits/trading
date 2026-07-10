"""Unit tests for execution validator."""

from __future__ import annotations

from core.context.audit_context import AuditContext
from core.context.core_context import CoreContext
from core.context.execution_context import ExecutionContext as CoreExecutionContext
from core.context.identity_context import IdentityContext
from core.context.operation_context import OperationContext
from core.context.request_context import RequestContext
from core.context.security_context import SecurityContext
from execution import ExecutionValidator
from tests.execution_helpers import (
    make_approved_risk_result,
    make_execution_context,
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


def test_validator_approved_risk_passes() -> None:
    validator = ExecutionValidator()
    context = make_execution_context().model_copy(update={"core_context": _make_core_context()})
    result = validator.validate(
        execution_id="exec-1",
        risk_result=make_approved_risk_result(),
        context=context,
    )
    assert result.valid is True
    assert result.policy_compliant is True


def test_validator_rejected_risk_fails() -> None:
    validator = ExecutionValidator()
    context = make_execution_context(risk_result=make_rejected_risk_result()).model_copy(
        update={"core_context": _make_core_context()}
    )
    result = validator.validate(
        execution_id="exec-1",
        risk_result=make_rejected_risk_result(),
        context=context,
    )
    assert result.valid is False
    assert "approved" in result.errors[0]


def test_validator_missing_risk_fails() -> None:
    validator = ExecutionValidator()
    context = make_execution_context()
    result = validator.validate(
        execution_id="exec-1",
        risk_result=None,
        context=context,
    )
    assert result.valid is False


def test_validator_missing_context_fails() -> None:
    validator = ExecutionValidator()
    result = validator.validate(
        execution_id="exec-1",
        risk_result=make_approved_risk_result(),
        context=None,
    )
    assert result.valid is False


def test_validator_context_id_mismatch_fails() -> None:
    validator = ExecutionValidator()
    context = make_execution_context(execution_id="other-id")
    result = validator.validate(
        execution_id="exec-1",
        risk_result=make_approved_risk_result(),
        context=context,
    )
    assert result.valid is False
