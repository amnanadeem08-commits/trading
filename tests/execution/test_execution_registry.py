"""Unit tests for execution registry."""

from __future__ import annotations

import pytest

from execution import (
    ExecutionRegistry,
    ExecutionState,
    get_execution_registry,
    reset_execution_registry,
)
from execution.exceptions import ExecutionNotFoundError
from tests.execution_helpers import SampleExecutionEngine, make_engine_metadata


def test_registry_lifecycle_state() -> None:
    registry = ExecutionRegistry()
    registry.register(make_engine_metadata())
    assert registry.get_engine_state("sample-engine") == ExecutionState.CREATED
    registry.set_engine_state("sample-engine", ExecutionState.VALIDATED)
    assert registry.get_engine_state("sample-engine") == ExecutionState.VALIDATED


def test_registry_track_execution() -> None:
    registry = ExecutionRegistry()
    registry.register(make_engine_metadata())
    registry.track_execution("exec-1", engine_id="sample-engine", state=ExecutionState.CREATED)
    assert registry.get_execution_state("exec-1") == ExecutionState.CREATED
    registry.set_execution_state("exec-1", ExecutionState.COMPLETED)
    assert registry.get_execution_state("exec-1") == ExecutionState.COMPLETED


def test_registry_version_tracking() -> None:
    registry = ExecutionRegistry()
    registry.register(make_engine_metadata(version="2.0.0"))
    assert registry.get_version("sample-engine") == "2.0.0"


def test_registry_unregister() -> None:
    registry = ExecutionRegistry()
    registry.register(make_engine_metadata())
    registry.unregister("sample-engine")
    with pytest.raises(ExecutionNotFoundError):
        registry.resolve("sample-engine")


def test_registry_list() -> None:
    registry = ExecutionRegistry()
    registry.register(make_engine_metadata(engine_id="engine-a"))
    registry.register_type(SampleExecutionEngine)
    assert "engine-a" in registry.list()
    assert "sample-engine" in registry.list_types()


def test_singleton_registry() -> None:
    reset_execution_registry()
    registry = get_execution_registry()
    registry.register(make_engine_metadata(engine_id="singleton"))
    assert get_execution_registry().list() == ("singleton",)
    reset_execution_registry()
