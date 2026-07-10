"""Contract tests for inference pipeline."""

from __future__ import annotations

import inspect

import pytest

from inference_pipeline import (
    InferenceBatchRequest,
    InferenceDispatcher,
    InferenceLifecycleManager,
    InferenceMetricsCollector,
    InferenceQueue,
    InferenceRegistry,
    InferenceRequest,
    InferenceResponse,
    InferenceRuntime,
    InferenceScheduler,
    InferenceValidator,
    InferenceVersionRegistry,
    ModelLoader,
    build_inference_runtime,
    prepare_production_model,
    run_inference_for_model,
)


@pytest.mark.contract
def test_inference_request_contract() -> None:
    fields = set(InferenceRequest.model_fields)
    assert "request_id" in fields
    assert "model_id" in fields
    assert "input_metadata" in fields


@pytest.mark.contract
def test_inference_response_contract() -> None:
    fields = set(InferenceResponse.model_fields)
    assert "status" in fields
    assert "metadata" in fields


@pytest.mark.contract
def test_model_loader_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(ModelLoader, predicate=inspect.isfunction)}
    assert "resolve_production_version" in methods
    assert "load_artifact_reference" in methods
    assert "validate_production_stage" in methods


@pytest.mark.contract
def test_inference_scheduler_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(InferenceScheduler, predicate=inspect.isfunction)
    }
    assert "submit" in methods
    assert "run_next" in methods
    assert "submit_batch" in methods


@pytest.mark.contract
def test_inference_queue_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(InferenceQueue, predicate=inspect.isfunction)}
    assert "enqueue" in methods
    assert "dequeue" in methods


@pytest.mark.contract
def test_inference_dispatcher_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(InferenceDispatcher, predicate=inspect.isfunction)
    }
    assert "dispatch" in methods
    assert "cancel" in methods


@pytest.mark.contract
def test_inference_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(InferenceRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods
    assert "history" in methods
    assert "latest" in methods
    assert "clear" in methods


@pytest.mark.contract
def test_inference_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(InferenceValidator, predicate=inspect.isfunction)
    }
    assert "validate_request" in methods
    assert "validate_production_version" in methods


@pytest.mark.contract
def test_inference_lifecycle_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(InferenceLifecycleManager, predicate=inspect.isfunction)
    }
    assert "emit_queued" in methods
    assert "emit_completed" in methods
    assert "emit_model_resolved" in methods


@pytest.mark.contract
def test_inference_metrics_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(InferenceMetricsCollector, predicate=inspect.isfunction)
    }
    assert "record_latency" in methods
    assert "statistics" in methods


@pytest.mark.contract
def test_inference_version_registry_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(InferenceVersionRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "latest" in methods


@pytest.mark.contract
def test_inference_runtime_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(InferenceRuntime, predicate=inspect.isfunction)
    }
    assert "submit" in methods
    assert "run_pending" in methods
    assert "resolve_model" in methods


@pytest.mark.contract
def test_batch_request_contract() -> None:
    fields = set(InferenceBatchRequest.model_fields)
    assert "batch_id" in fields
    assert "input_metadata_batch" in fields


@pytest.mark.contract
def test_integration_bridge_exports() -> None:
    assert callable(build_inference_runtime)
    assert callable(prepare_production_model)
    assert callable(run_inference_for_model)
