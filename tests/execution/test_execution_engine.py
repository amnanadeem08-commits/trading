"""Unit tests for execution engine."""

from __future__ import annotations

import pytest

from execution import ExecutionState
from execution.exceptions import ExecutionNotFoundError, ExecutionRegistrationError
from execution.registry.execution_registry import ExecutionRegistry
from tests.execution_helpers import (
    FailingExecutionEngine,
    SampleExecutionEngine,
    make_engine_metadata,
    make_execution_context,
)


def test_engine_metadata() -> None:
    engine = SampleExecutionEngine()
    metadata = engine.metadata()
    assert metadata.engine_id == "sample-engine"
    assert metadata.version == "1.0.0"


def test_engine_execute() -> None:
    engine = SampleExecutionEngine()
    context = make_execution_context()
    result = engine.execute(context)
    assert result.state == ExecutionState.COMPLETED
    assert result.output["prepared"] is True


def test_registry_register_and_resolve() -> None:
    registry = ExecutionRegistry()
    registry.register(make_engine_metadata())
    metadata = registry.resolve("sample-engine")
    assert metadata.name == "Sample Engine"


def test_registry_register_type() -> None:
    registry = ExecutionRegistry()
    registry.register_type(SampleExecutionEngine)
    assert registry.exists("sample-engine")
    engine_type = registry.resolve_type("sample-engine")
    assert engine_type is SampleExecutionEngine


def test_registry_duplicate_registration_raises() -> None:
    registry = ExecutionRegistry()
    registry.register(make_engine_metadata())
    with pytest.raises(ExecutionRegistrationError):
        registry.register(make_engine_metadata())


def test_registry_not_found_raises() -> None:
    registry = ExecutionRegistry()
    with pytest.raises(ExecutionNotFoundError):
        registry.resolve("missing")


def test_failing_engine_raises() -> None:
    engine = FailingExecutionEngine()
    with pytest.raises(RuntimeError, match="execution preparation failed"):
        engine.execute(make_execution_context(execution_id="fail-1"))
