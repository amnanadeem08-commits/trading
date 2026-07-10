"""Extended unit tests for ML runtime coverage."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from ml_runtime import (
    ExecutionStatus,
    RuntimeLifecycleEventType,
    RuntimeLifecycleManager,
    RuntimeSessionError,
)
from tests.ml_runtime_helpers import StubModelExecutor, make_ml_runtime, run_full_runtime_flow


@pytest.mark.unit
def test_executor_execute_failure_path() -> None:
    runtime = make_ml_runtime()
    runtime.registry.unregister_executor("stub-executor")
    runtime.register_executor(
        StubModelExecutor(executor_id="stub-executor", fail_on_execute=True),
        name="Failing Stub",
        version="1.0.0",
    )
    inference_response, _ = run_full_runtime_flow()
    result = runtime.execute(inference_response, executor_id="stub-executor")
    assert result.status == ExecutionStatus.FAILED


@pytest.mark.unit
def test_lifecycle_runtime_started_completed_failed() -> None:
    lifecycle = RuntimeLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_runtime_started(
        execution_id="exec-1",
        request_id="req-1",
        model_id="model-1",
        executor_id="executor-1",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_runtime_completed(
        execution_id="exec-1",
        request_id="req-1",
        model_id="model-1",
        executor_id="executor-1",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_runtime_failed(
        execution_id="exec-2",
        request_id="req-2",
        model_id="model-1",
        message="failed",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_runtime_shutdown(correlation_id="c", trace_id="t")
    types = {event.event_type for event in lifecycle.events}
    assert RuntimeLifecycleEventType.RUNTIME_STARTED in types
    assert RuntimeLifecycleEventType.RUNTIME_COMPLETED in types
    assert RuntimeLifecycleEventType.RUNTIME_FAILED in types
    assert RuntimeLifecycleEventType.RUNTIME_SHUTDOWN in types


@pytest.mark.unit
def test_register_executor_type_error() -> None:
    runtime = make_ml_runtime()
    with pytest.raises(TypeError):
        runtime.register_executor(object(), name="Bad", version="1.0.0")


@pytest.mark.unit
def test_session_get_missing() -> None:
    runtime = make_ml_runtime()
    with pytest.raises(RuntimeSessionError):
        runtime.session_manager.get("missing")
