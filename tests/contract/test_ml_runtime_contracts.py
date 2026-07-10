"""Contract tests for ML runtime public API."""

from __future__ import annotations

import inspect

import pytest

from ml_runtime import (
    ExecutionMetadata,
    ExecutionResult,
    MLRuntime,
    ModelExecutor,
    RuntimeContext,
    RuntimeLifecycleManager,
    RuntimeMetricsCollector,
    RuntimeRegistry,
    RuntimeSessionManager,
    RuntimeValidator,
    RuntimeVersionRegistry,
    build_ml_runtime,
    execute_runtime_for_inference,
    run_inference_and_execute,
)


@pytest.mark.contract
def test_ml_runtime_public_exports() -> None:
    assert MLRuntime is not None
    assert ModelExecutor is not None
    assert callable(build_ml_runtime)
    assert callable(execute_runtime_for_inference)
    assert callable(run_inference_and_execute)


@pytest.mark.contract
def test_model_executor_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(ModelExecutor, predicate=inspect.isfunction)}
    assert "load" in methods
    assert "execute" in methods
    assert "execute_batch" in methods
    assert "unload" in methods
    assert "health" in methods


@pytest.mark.contract
def test_runtime_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(RuntimeRegistry, predicate=inspect.isfunction)
    }
    assert "register_executor" in methods
    assert "unregister_executor" in methods
    assert "lookup" in methods
    assert "list" in methods
    assert "clear" in methods


@pytest.mark.contract
def test_execution_result_metadata_only() -> None:
    fields = set(ExecutionResult.model_fields)
    assert "execution_id" in fields
    assert "status" in fields
    assert "metadata" in fields
    metadata_fields = set(ExecutionMetadata.model_fields)
    assert "artifact_reference" in metadata_fields
    assert "model_version" in metadata_fields


@pytest.mark.contract
def test_runtime_components_contract() -> None:
    assert RuntimeContext is not None
    assert RuntimeSessionManager is not None
    assert RuntimeValidator is not None
    assert RuntimeMetricsCollector is not None
    assert RuntimeLifecycleManager is not None
    assert RuntimeVersionRegistry is not None
