"""Helpers for execution layer tests."""

from __future__ import annotations

from typing import Any

from decision.engine.decision_result import DecisionResult
from decision.engine.decision_state import DecisionState
from execution.engine.execution_context import ExecutionContext
from execution.engine.execution_engine import ExecutionEngine, ExecutionEngineMetadata
from execution.engine.execution_result import ExecutionResult
from execution.engine.execution_state import ExecutionState
from risk.engine.risk_result import RiskResult
from risk.engine.risk_state import RiskState


def make_engine_metadata(
    *,
    engine_id: str = "sample-engine",
    name: str = "Sample Engine",
    version: str = "1.0.0",
) -> ExecutionEngineMetadata:
    return ExecutionEngineMetadata(
        engine_id=engine_id,
        name=name,
        version=version,
        capabilities=("prepare",),
        tags=("test",),
    )


def make_decision_result(
    *,
    decision_id: str = "dec-1",
    confidence: float = 0.85,
) -> DecisionResult:
    return DecisionResult(
        decision_id=decision_id,
        engine_id="decision-engine",
        state=DecisionState.COMPLETED,
        output={"outcome": "approved", "confidence": confidence},
        confidence=confidence,
    )


def make_approved_risk_result(
    *,
    risk_id: str = "risk-1",
    engine_id: str = "risk-engine",
) -> RiskResult:
    return RiskResult(
        risk_id=risk_id,
        engine_id=engine_id,
        policy_id="sample-policy",
        state=RiskState.APPROVED,
        output={"approved": True},
        metadata={"source": "test"},
        validation={"passed": True},
        version_info={"engine_version": "1.0.0"},
    )


def make_rejected_risk_result(
    *,
    risk_id: str = "risk-1",
) -> RiskResult:
    return RiskResult(
        risk_id=risk_id,
        engine_id="risk-engine",
        state=RiskState.REJECTED,
        output={"approved": False},
        validation={"passed": False},
    )


class SampleExecutionEngine(ExecutionEngine):
    """Concrete execution engine used in unit tests."""

    def engine_id(self) -> str:
        return "sample-engine"

    def name(self) -> str:
        return "Sample Engine"

    def version(self) -> str:
        return "1.0.0"

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        return ExecutionResult(
            execution_id=context.execution_id,
            engine_id=self.engine_id(),
            state=ExecutionState.COMPLETED,
            output={"prepared": True, "execution_id": context.execution_id},
            metadata={"engine": self.name()},
            version_info={"engine_version": self.version()},
        )


class FailingExecutionEngine(ExecutionEngine):
    """Execution engine that fails during preparation."""

    def engine_id(self) -> str:
        return "failing-engine"

    def name(self) -> str:
        return "Failing Engine"

    def version(self) -> str:
        return "1.0.0"

    def execute(self, context: ExecutionContext) -> ExecutionResult:
        raise RuntimeError("execution preparation failed")


def make_execution_context(
    *,
    execution_id: str = "exec-1",
    risk_result: RiskResult | None = None,
    decision_result: DecisionResult | None = None,
    input_data: dict[str, Any] | None = None,
) -> ExecutionContext:
    return ExecutionContext(
        execution_id=execution_id,
        correlation_id="corr-1",
        trace_id="trace-1",
        risk_result=risk_result or make_approved_risk_result(),
        decision_result=decision_result or make_decision_result(),
        input_data=input_data or {},
    )
