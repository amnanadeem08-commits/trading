"""Contract tests for training pipeline."""

from __future__ import annotations

import inspect

import pytest

from training_pipeline import (
    ArtifactStore,
    CheckpointRegistry,
    DatasetSelector,
    ExperimentRegistry,
    TrainingDispatcher,
    TrainingJob,
    TrainingLifecycleManager,
    TrainingMetricsCollector,
    TrainingPipelineRuntime,
    TrainingQueue,
    TrainingRegistry,
    TrainingScheduler,
    TrainingValidator,
    TrainingVersionRegistry,
    build_training_runtime,
    schedule_training_from_dataset,
)


@pytest.mark.contract
def test_training_job_contract() -> None:
    fields = set(TrainingJob.model_fields)
    assert "spec" in fields
    assert "status" in fields
    assert "created_at" in fields


@pytest.mark.contract
def test_training_scheduler_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(TrainingScheduler, predicate=inspect.isfunction)
    }
    assert "submit" in methods
    assert "run_next" in methods
    assert "run_all" in methods


@pytest.mark.contract
def test_training_queue_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(TrainingQueue, predicate=inspect.isfunction)}
    assert "enqueue" in methods
    assert "dequeue" in methods
    assert "get" in methods


@pytest.mark.contract
def test_dataset_selector_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(DatasetSelector, predicate=inspect.isfunction)
    }
    assert "resolve_reference" in methods
    assert "capture_snapshot" in methods
    assert "list_available" in methods


@pytest.mark.contract
def test_experiment_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(ExperimentRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "lookup" in methods
    assert "record_run" in methods


@pytest.mark.contract
def test_artifact_store_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(ArtifactStore, predicate=inspect.isfunction)}
    assert "store" in methods
    assert "get" in methods
    assert "list_artifacts" in methods


@pytest.mark.contract
def test_checkpoint_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(CheckpointRegistry, predicate=inspect.isfunction)
    }
    assert "create" in methods
    assert "get" in methods
    assert "list_for_job" in methods


@pytest.mark.contract
def test_training_registry_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(TrainingRegistry, predicate=inspect.isfunction)
    }
    assert "register_job" in methods
    assert "update_job" in methods
    assert "get" in methods


@pytest.mark.contract
def test_training_validator_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(TrainingValidator, predicate=inspect.isfunction)
    }
    assert "validate_request" in methods
    assert "validate_spec" in methods
    assert "validate_job" in methods


@pytest.mark.contract
def test_training_lifecycle_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(TrainingLifecycleManager, predicate=inspect.isfunction)
    }
    assert "emit_queued" in methods
    assert "emit_started" in methods
    assert "emit_completed" in methods
    assert "emit_failed" in methods


@pytest.mark.contract
def test_training_metrics_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(TrainingMetricsCollector, predicate=inspect.isfunction)
    }
    assert "record_status" in methods
    assert "statistics" in methods


@pytest.mark.contract
def test_training_dispatcher_contract() -> None:
    methods = {
        name for name, _ in inspect.getmembers(TrainingDispatcher, predicate=inspect.isfunction)
    }
    assert "dispatch" in methods
    assert "cancel" in methods


@pytest.mark.contract
def test_training_version_registry_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(TrainingVersionRegistry, predicate=inspect.isfunction)
    }
    assert "register" in methods
    assert "get" in methods
    assert "latest_for_job" in methods


@pytest.mark.contract
def test_training_runtime_contract() -> None:
    methods = {
        name
        for name, _ in inspect.getmembers(TrainingPipelineRuntime, predicate=inspect.isfunction)
    }
    assert "submit_training" in methods
    assert "schedule" in methods
    assert "run_pending" in methods


@pytest.mark.contract
def test_integration_bridge_exports() -> None:
    assert callable(build_training_runtime)
    assert callable(schedule_training_from_dataset)
