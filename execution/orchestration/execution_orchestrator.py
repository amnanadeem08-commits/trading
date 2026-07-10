"""Execution orchestrator."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from core.context.core_context import CoreContext
from decision.engine.decision_result import DecisionResult
from execution.dispatch.dispatcher import Dispatcher
from execution.engine.execution_context import ExecutionContext
from execution.engine.execution_engine import ExecutionEngine
from execution.engine.execution_result import ExecutionResult
from execution.engine.execution_state import ExecutionState
from execution.exceptions import ExecutionNotFoundError, OrchestrationError
from execution.lifecycle.execution_lifecycle_manager import (
    ExecutionLifecycleEventType,
    ExecutionLifecycleManager,
)
from execution.registry.execution_registry import ExecutionRegistry
from execution.validation.execution_validator import ExecutionValidator
from risk.engine.risk_result import RiskResult


class ExecutionOrchestrator:
    """Coordinates execution: validation -> context -> queue -> dispatch -> result."""

    def __init__(
        self,
        *,
        engine_registry: ExecutionRegistry | None = None,
        validator: ExecutionValidator | None = None,
        dispatcher: Dispatcher | None = None,
        lifecycle: ExecutionLifecycleManager | None = None,
    ) -> None:
        self._engines = engine_registry or ExecutionRegistry()
        self._validator = validator or ExecutionValidator()
        self._dispatcher = dispatcher or Dispatcher()
        self._lifecycle = lifecycle

    def create_context(
        self,
        *,
        execution_id: str | None = None,
        core_context: CoreContext | None = None,
        risk_result: RiskResult | None = None,
        decision_result: DecisionResult | None = None,
        input_data: dict[str, Any] | None = None,
    ) -> ExecutionContext:
        resolved_id = execution_id or str(uuid4())
        correlation_id = core_context.correlation_id if core_context else str(uuid4())
        trace_id = core_context.trace_id if core_context else str(uuid4())
        return ExecutionContext(
            execution_id=resolved_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            core_context=core_context,
            risk_result=risk_result,
            decision_result=decision_result,
            input_data=input_data or {},
        )

    def execute(
        self,
        context: ExecutionContext,
        engine: ExecutionEngine,
        *,
        priority: int = 0,
    ) -> ExecutionResult:
        """Execute the pipeline: validation -> context -> queue -> dispatch -> result."""
        engine_id = engine.engine_id()
        execution_id = context.execution_id
        if not self._engines.exists(engine_id):
            raise ExecutionNotFoundError(engine_id)

        self._emit_lifecycle(
            ExecutionLifecycleEventType.EXECUTION_STARTED,
            execution_id=execution_id,
            context=context,
            message="execution started",
        )
        self._engines.track_execution(
            execution_id, engine_id=engine_id, state=ExecutionState.CREATED
        )
        self._engines.set_engine_state(engine_id, ExecutionState.CREATED)

        try:
            validation_result = self._validator.validate(
                execution_id=execution_id,
                risk_result=context.risk_result,
                context=context,
            )
            self._emit_lifecycle(
                ExecutionLifecycleEventType.EXECUTION_VALIDATED,
                execution_id=execution_id,
                context=context,
                message="execution validated",
                payload={"valid": validation_result.valid},
            )
            if not validation_result.valid:
                self._engines.set_execution_state(execution_id, ExecutionState.FAILED)
                self._engines.set_engine_state(engine_id, ExecutionState.FAILED)
                self._emit_lifecycle(
                    ExecutionLifecycleEventType.EXECUTION_FAILED,
                    execution_id=execution_id,
                    context=context,
                    message="validation failed",
                    payload={"errors": list(validation_result.errors)},
                )
                return self._build_failed_result(
                    context=context,
                    engine_id=engine_id,
                    validation_result=validation_result,
                    reason="validation_failed",
                )

            self._engines.set_execution_state(execution_id, ExecutionState.VALIDATED)
            self._engines.set_engine_state(engine_id, ExecutionState.VALIDATED)
            engine_result = engine.execute(context)

            dispatch_request = self._dispatcher.create_request(
                execution_id=execution_id,
                engine_id=engine_id,
                context=context,
                payload=engine_result.output,
                priority=priority,
            )
            self._dispatcher.enqueue(dispatch_request)
            self._engines.set_execution_state(execution_id, ExecutionState.QUEUED)
            self._engines.set_engine_state(engine_id, ExecutionState.QUEUED)
            self._emit_lifecycle(
                ExecutionLifecycleEventType.EXECUTION_QUEUED,
                execution_id=execution_id,
                context=context,
                message="execution queued",
            )

            dispatch_result = self._dispatcher.dispatch(dispatch_request)
            self._engines.set_execution_state(execution_id, ExecutionState.DISPATCHED)
            self._engines.set_engine_state(engine_id, ExecutionState.DISPATCHED)
            self._emit_lifecycle(
                ExecutionLifecycleEventType.EXECUTION_DISPATCHED,
                execution_id=execution_id,
                context=context,
                message="execution dispatched",
            )

            merged = self._merge_result(
                context=context,
                engine_result=engine_result,
                validation_result=validation_result,
                dispatch_result=dispatch_result,
            )
            self._engines.set_execution_state(execution_id, ExecutionState.COMPLETED)
            self._engines.set_engine_state(engine_id, ExecutionState.COMPLETED)
            self._emit_lifecycle(
                ExecutionLifecycleEventType.EXECUTION_COMPLETED,
                execution_id=execution_id,
                context=context,
                message="execution completed",
            )
            return merged
        except ExecutionNotFoundError:
            raise
        except Exception as error:
            self._engines.set_execution_state(execution_id, ExecutionState.FAILED)
            self._engines.set_engine_state(engine_id, ExecutionState.FAILED)
            self._emit_lifecycle(
                ExecutionLifecycleEventType.EXECUTION_FAILED,
                execution_id=execution_id,
                context=context,
                message="execution failed",
                payload={"error": str(error)},
            )
            msg = f"Execution orchestration failed: {error}"
            raise OrchestrationError(msg) from error

    def cancel(self, context: ExecutionContext, engine_id: str) -> ExecutionResult:
        """Cancel an execution operation."""
        execution_id = context.execution_id
        self._engines.set_execution_state(execution_id, ExecutionState.CANCELLED)
        self._engines.set_engine_state(engine_id, ExecutionState.CANCELLED)
        self._emit_lifecycle(
            ExecutionLifecycleEventType.EXECUTION_CANCELLED,
            execution_id=execution_id,
            context=context,
            message="execution cancelled",
        )
        return ExecutionResult(
            execution_id=execution_id,
            engine_id=engine_id,
            state=ExecutionState.CANCELLED,
            output={"cancelled": True},
            metadata={"reason": "cancelled"},
        )

    def _emit_lifecycle(
        self,
        event_type: ExecutionLifecycleEventType,
        *,
        execution_id: str,
        context: ExecutionContext,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        if self._lifecycle is None:
            return
        self._lifecycle.emit(
            event_type,
            execution_id=execution_id,
            correlation_id=context.correlation_id,
            trace_id=context.trace_id,
            message=message,
            payload=payload,
        )

    def _build_failed_result(
        self,
        *,
        context: ExecutionContext,
        engine_id: str,
        validation_result: Any,
        reason: str,
    ) -> ExecutionResult:
        return ExecutionResult(
            execution_id=context.execution_id,
            engine_id=engine_id,
            state=ExecutionState.FAILED,
            output={"failed": True, "reason": reason},
            metadata={"reason": reason},
            validation={
                "valid": validation_result.valid,
                "errors": list(validation_result.errors),
                "checks": dict(validation_result.checks),
            },
        )

    def _merge_result(
        self,
        *,
        context: ExecutionContext,
        engine_result: ExecutionResult,
        validation_result: Any,
        dispatch_result: Any,
    ) -> ExecutionResult:
        return ExecutionResult(
            execution_id=context.execution_id,
            engine_id=engine_result.engine_id,
            state=ExecutionState.COMPLETED,
            output=engine_result.output,
            metadata=engine_result.metadata,
            dispatch={
                "request_id": dispatch_result.request_id,
                "success": dispatch_result.success,
                "output": dict(dispatch_result.output),
            },
            validation={
                "valid": validation_result.valid,
                "checks": dict(validation_result.checks),
            },
            version_info=dict(engine_result.version_info),
        )
