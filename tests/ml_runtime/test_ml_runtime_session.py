"""Unit tests for runtime sessions."""

from __future__ import annotations

import pytest

from ml_runtime import ExecutionStatus, RuntimeSessionError
from ml_runtime.runtime.runtime_session import RuntimeSessionManager


@pytest.mark.unit
def test_session_create_and_update() -> None:
    manager = RuntimeSessionManager(max_sessions=2)
    session = manager.create(
        request_id="req-1",
        model_id="model-1",
        executor_id="executor-1",
    )
    assert session.status == ExecutionStatus.PENDING
    updated = manager.update(session.session_id, status=ExecutionStatus.RUNNING)
    assert updated.status == ExecutionStatus.RUNNING


@pytest.mark.unit
def test_session_capacity_limit() -> None:
    manager = RuntimeSessionManager(max_sessions=1)
    manager.create(request_id="req-1", model_id="model-1", executor_id="executor-1")
    with pytest.raises(RuntimeSessionError):
        manager.create(request_id="req-2", model_id="model-1", executor_id="executor-1")


@pytest.mark.unit
def test_session_build_context() -> None:
    manager = RuntimeSessionManager()
    session = manager.create(
        request_id="req-1",
        model_id="model-1",
        executor_id="executor-1",
    )
    context = manager.build_context(
        session,
        input_metadata={"id": "1"},
        model_version="v-1",
        artifact_reference="artifact-1",
        correlation_id="c",
        trace_id="t",
    )
    assert context.model_version == "v-1"
    assert context.artifact_reference == "artifact-1"
