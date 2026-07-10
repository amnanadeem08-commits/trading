"""Unit tests for runtime registries."""

from __future__ import annotations

import pytest

from ml_runtime import ExecutorNotFoundError, RuntimeRegistry
from tests.ml_runtime_helpers import StubModelExecutor


@pytest.mark.unit
def test_runtime_registry_register_and_lookup() -> None:
    registry = RuntimeRegistry()
    executor = StubModelExecutor(executor_id="exec-1")
    metadata = registry.register_executor(
        executor,
        name="Stub",
        version="1.0.0",
    )
    assert metadata.executor_id == "exec-1"
    assert registry.lookup("exec-1") is executor
    assert len(registry.list()) == 1


@pytest.mark.unit
def test_runtime_registry_unregister_and_clear() -> None:
    registry = RuntimeRegistry()
    registry.register_executor(StubModelExecutor(), name="Stub", version="1.0.0")
    registry.unregister_executor("stub-executor")
    assert registry.list() == ()
    registry.register_executor(StubModelExecutor(), name="Stub", version="1.0.0")
    registry.clear()
    assert registry.list() == ()


@pytest.mark.unit
def test_runtime_registry_lookup_missing() -> None:
    registry = RuntimeRegistry()
    with pytest.raises(ExecutorNotFoundError):
        registry.lookup("missing")
