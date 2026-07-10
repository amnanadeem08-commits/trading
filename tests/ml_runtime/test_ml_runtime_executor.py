"""Unit tests for model executor interface."""

from __future__ import annotations

import pytest

from ml_runtime import ModelExecutor
from ml_runtime.execution.model_executor import ModelExecutor as ModelExecutorBase
from tests.ml_runtime_helpers import StubModelExecutor


@pytest.mark.unit
def test_stub_executor_implements_interface() -> None:
    executor = StubModelExecutor()
    assert isinstance(executor, ModelExecutor)
    assert isinstance(executor, ModelExecutorBase)


@pytest.mark.unit
def test_stub_executor_lifecycle() -> None:
    executor = StubModelExecutor()
    executor.load(artifact_reference="artifact-1", metadata={"model_id": "model-1"})
    assert executor.loaded is True
    health = executor.health()
    assert health["status"] == "healthy"
    executor.unload()
    assert executor.unloaded is True


@pytest.mark.unit
def test_stub_executor_execute_batch() -> None:
    from ml_runtime.runtime.runtime_context import RuntimeContext

    executor = StubModelExecutor()
    context = RuntimeContext(
        session_id="session-1",
        request_id="req-1",
        model_id="model-1",
        model_version="v-1",
        artifact_reference="artifact-1",
        executor_id="stub-executor",
        input_metadata={"id": "1"},
        correlation_id="c",
        trace_id="t",
    )
    results = executor.execute_batch((context,))
    assert len(results) == 1
    assert results[0].status.value == "completed"
