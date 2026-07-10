"""Unit tests for decision context."""

from __future__ import annotations

from ai.reasoning.reasoning_result import ReasoningResult
from core.context.audit_context import AuditContext
from core.context.core_context import CoreContext
from core.context.execution_context import ExecutionContext
from core.context.identity_context import IdentityContext
from core.context.operation_context import OperationContext
from core.context.request_context import RequestContext
from core.context.security_context import SecurityContext
from decision import DecisionContext
from ml.inference.prediction_result import PredictionResult


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


def test_decision_context_fields() -> None:
    context = DecisionContext(
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        input_data={"key": "value"},
        metadata={"source": "test"},
    )
    assert context.decision_id == "dec-1"
    assert context.input_data["key"] == "value"
    assert context.ai_result is None
    assert context.ml_result is None


def test_decision_context_with_ai_and_ml() -> None:
    core = _make_core_context()
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
        outputs=({"prediction": 0.8},),
    )
    context = DecisionContext(
        decision_id="dec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        core_context=core,
        ai_result=ai_result,
        ml_result=ml_result,
    )
    assert context.core_context is not None
    assert context.ai_result.confidence == 0.9
    assert context.ml_result.model_id == "model-1"
