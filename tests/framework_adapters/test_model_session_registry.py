"""Unit tests for model session registry."""

from __future__ import annotations

import pytest

from framework_adapters import (
    EngineType,
    ModelRuntimeState,
    ModelSessionRecord,
    ModelSessionRegistry,
    build_model_session_key,
)
from framework_adapters.adapters.stub_executor_factory import StubExecutorFactory
from models.common import utc_now


def _make_record(*, adapter_id: str = "stub-framework-adapter") -> ModelSessionRecord:
    return ModelSessionRecord(
        session_id="session-1",
        model_id="model-1",
        artifact_id="artifact-1",
        adapter_id=adapter_id,
        framework=EngineType.STUB.value,
        executor_id=adapter_id,
        loaded_at=utc_now(),
        state=ModelRuntimeState.READY,
        cached=True,
    )


@pytest.mark.unit
def test_build_model_session_key_is_deterministic() -> None:
    key = build_model_session_key(
        model_id="model-1",
        artifact_id="artifact-1",
        adapter_id="stub-framework-adapter",
        model_version="1.0.0",
    )
    assert key == "model-1:artifact-1:stub-framework-adapter:1.0.0"


@pytest.mark.unit
def test_registry_register_lookup_and_replace() -> None:
    registry = ModelSessionRegistry()
    record = _make_record()
    executor = StubExecutorFactory().create(executor_id="stub-framework-adapter")
    session_key = build_model_session_key(
        model_id=record.model_id,
        artifact_id=record.artifact_id,
        adapter_id=record.adapter_id,
        model_version=record.model_version,
    )
    registry.register(session_key=session_key, record=record, executor=executor)
    assert registry.lookup(session_key) == record
    assert registry.get_executor(session_key).executor_id() == "stub-framework-adapter"

    replacement = StubExecutorFactory().create(executor_id="replacement")
    updated = registry.replace_executor(
        session_key,
        executor=replacement,
        record_updates={"execution_count": 2},
    )
    assert updated.execution_count == 2
    assert registry.get_executor(session_key).executor_id() == "replacement"


@pytest.mark.unit
def test_registry_reference_count_and_filters() -> None:
    registry = ModelSessionRegistry()
    record = _make_record()
    executor = StubExecutorFactory().create(executor_id="stub-framework-adapter")
    session_key = build_model_session_key(
        model_id=record.model_id,
        artifact_id=record.artifact_id,
        adapter_id=record.adapter_id,
        model_version=record.model_version,
    )
    registry.register(session_key=session_key, record=record, executor=executor)
    incremented = registry.increment_ref_count(session_key)
    assert incremented.reference_count == 2
    decremented = registry.decrement_ref_count(session_key)
    assert decremented.reference_count == 1
    assert registry.list_by_model_id("model-1")[0].model_id == "model-1"
    assert registry.list_by_state(ModelRuntimeState.READY)[0].state == ModelRuntimeState.READY
