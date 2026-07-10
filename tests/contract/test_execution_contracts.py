"""Contract tests for execution layer."""

from __future__ import annotations

import inspect

import pytest

from execution import (
    Dispatcher,
    DispatchQueue,
    ExecutionContext,
    ExecutionEngine,
    ExecutionOrchestrator,
    ExecutionRegistry,
    ExecutionResult,
    ExecutionState,
    ExecutionValidator,
    ExecutionVersion,
)
from tests.execution_helpers import SampleExecutionEngine, make_execution_context


@pytest.mark.contract
def test_execution_engine_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ExecutionEngine, predicate=inspect.isfunction)
    }
    assert "execute" in methods
    assert "engine_id" in methods


@pytest.mark.contract
def test_sample_engine_contract_compliance() -> None:
    engine = SampleExecutionEngine()
    context = make_execution_context()
    result = engine.execute(context)
    assert isinstance(result, ExecutionResult)
    assert result.engine_id == "sample-engine"


@pytest.mark.contract
def test_execution_result_fields() -> None:
    result = ExecutionResult(
        execution_id="exec-1",
        engine_id="engine-1",
        validation={"valid": True},
        version_info={"engine_version": "1.0.0"},
    )
    assert result.execution_id == "exec-1"
    assert result.validation["valid"] is True


@pytest.mark.contract
def test_execution_context_fields() -> None:
    context = ExecutionContext(
        execution_id="exec-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    assert context.execution_id == "exec-1"


@pytest.mark.contract
def test_execution_state_values() -> None:
    states = {item.value for item in ExecutionState}
    assert states == {
        "created",
        "validated",
        "queued",
        "dispatched",
        "completed",
        "failed",
        "cancelled",
    }


@pytest.mark.contract
def test_orchestrator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ExecutionOrchestrator, predicate=inspect.isfunction)
    }
    assert "create_context" in methods
    assert "execute" in methods


@pytest.mark.contract
def test_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ExecutionValidator, predicate=inspect.isfunction)
    }
    assert "validate" in methods


@pytest.mark.contract
def test_dispatcher_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(Dispatcher, predicate=inspect.isfunction)}
    assert "create_request" in methods
    assert "dispatch" in methods
    assert "enqueue" in methods


@pytest.mark.contract
def test_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ExecutionRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "resolve" in methods


@pytest.mark.contract
def test_version_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ExecutionVersion, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "is_compatible" in methods


@pytest.mark.contract
def test_dispatch_queue_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(DispatchQueue, predicate=inspect.isfunction)}
    assert "enqueue" in methods
    assert "dequeue" in methods
