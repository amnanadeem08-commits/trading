"""Extended unit tests for training pipeline coverage."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from tests.training_pipeline_helpers import (
    make_dataset_reference,
    make_training_job_spec,
    make_training_request,
    make_training_runtime,
    seed_feature_store_with_dataset,
)
from training_pipeline import (
    ArtifactStore,
    CheckpointNotFoundError,
    CheckpointRegistry,
    DatasetReferenceError,
    DatasetSelector,
    Experiment,
    ExperimentRegistry,
    TrainingJob,
    TrainingJobError,
    TrainingJobStatus,
    TrainingLifecycleManager,
    TrainingQueue,
    TrainingValidationError,
    TrainingValidator,
    TrainingVersionRegistry,
)


@pytest.mark.unit
def test_artifact_store_list_remove_and_validate() -> None:
    store = ArtifactStore()
    artifact = store.store(
        experiment_id="exp-1",
        run_id="run-1",
        job_id="job-1",
        model_family="baseline",
        training_version="1.0.0",
        dataset=make_dataset_reference(),
        hyperparameters={"epochs": 1},
    )
    assert len(store.list_artifacts()) == 1
    store.validate_manifest(artifact)
    store.remove(artifact.artifact_id)
    assert store.list_artifacts() == ()


@pytest.mark.unit
def test_artifact_store_validate_manifest_failure() -> None:
    store = ArtifactStore()
    artifact = store.store(
        experiment_id="exp-1",
        run_id="run-1",
        job_id="job-1",
        model_family="baseline",
        training_version="1.0.0",
        dataset=make_dataset_reference(),
        hyperparameters={},
    )
    broken = artifact.model_copy(
        update={"manifest": artifact.manifest.model_copy(update={"artifact_id": ""})}
    )
    with pytest.raises(TrainingJobError):
        store.validate_manifest(broken)


@pytest.mark.unit
def test_checkpoint_registry_remove_and_latest_error() -> None:
    registry = CheckpointRegistry()
    with pytest.raises(CheckpointNotFoundError):
        registry.latest_for_job("missing")
    checkpoint = registry.create(
        job_id="job-1",
        experiment_id="exp-1",
        run_id="run-1",
        status=TrainingJobStatus.RUNNING,
    )
    registry.remove(checkpoint.checkpoint_id)
    with pytest.raises(CheckpointNotFoundError):
        registry.get(checkpoint.checkpoint_id)


@pytest.mark.unit
def test_dataset_selector_snapshot_reference_and_list() -> None:
    store = seed_feature_store_with_dataset(record_count=2)
    selector = DatasetSelector(store)
    snapshot = selector.capture_snapshot("dataset-1")
    reference = selector.resolve_reference(
        dataset_id="dataset-1",
        snapshot_id=snapshot.snapshot_id,
    )
    assert reference.snapshot_id == snapshot.snapshot_id
    datasets = selector.list_available()
    assert len(datasets) == 1


@pytest.mark.unit
def test_dataset_selector_snapshot_mismatch_raises() -> None:
    store = seed_feature_store_with_dataset()
    selector = DatasetSelector(store)
    snapshot = selector.capture_snapshot("dataset-1")
    with pytest.raises(DatasetReferenceError):
        selector.resolve_reference(dataset_id="other", snapshot_id=snapshot.snapshot_id)


@pytest.mark.unit
def test_experiment_registry_validation_and_run_errors() -> None:
    registry = ExperimentRegistry()
    with pytest.raises(TrainingJobError):
        registry.register(Experiment.create(experiment_id="", name="bad", model_family="baseline"))
    with pytest.raises(TrainingJobError):
        registry.get_run("missing")


@pytest.mark.unit
def test_training_queue_peek_update_list() -> None:
    queue = TrainingQueue()
    job = TrainingJob.from_spec(make_training_job_spec(job_id="job-peek"))
    queue.enqueue(job)
    assert queue.peek() is not None
    completed = job.with_status(TrainingJobStatus.COMPLETED)
    queue.update(completed)
    assert queue.get("job-peek").status == TrainingJobStatus.COMPLETED
    assert len(queue.list_jobs()) == 1


@pytest.mark.unit
def test_training_dispatcher_validation_failure() -> None:
    runtime = make_training_runtime()
    bad_spec = make_training_job_spec(job_id="").model_copy(
        update={"dataset": make_dataset_reference(dataset_id="")}
    )
    bad_job = TrainingJob.from_spec(bad_spec)
    result = runtime.dispatcher.dispatch(bad_job)
    assert result.status == TrainingJobStatus.FAILED


@pytest.mark.unit
def test_training_dispatcher_cancel() -> None:
    runtime = make_training_runtime()
    job = TrainingJob.from_spec(make_training_job_spec(job_id="job-cancel"))
    cancelled = runtime.dispatcher.cancel(job)
    assert cancelled.status == TrainingJobStatus.CANCELLED


@pytest.mark.unit
def test_training_scheduler_validation_error() -> None:
    runtime = make_training_runtime()
    request = make_training_request().model_copy(update={"model_family": ""})
    with pytest.raises(TrainingValidationError):
        runtime.scheduler.submit(request)


@pytest.mark.unit
def test_training_scheduler_register_experiment() -> None:
    runtime = make_training_runtime()
    experiment = Experiment.create(
        experiment_id="registered-exp",
        name="Registered",
        model_family="baseline",
    )
    registered = runtime.scheduler.register_experiment(experiment)
    assert registered.experiment_id == "registered-exp"


@pytest.mark.unit
def test_training_validator_spec_and_experiment_paths() -> None:
    validator = TrainingValidator()
    registry = ExperimentRegistry()
    assert validator.validate_spec(make_training_job_spec(job_id="")).valid is False
    assert validator.validate_experiment_exists("missing", registry).valid is False
    registry.register(Experiment.create(experiment_id="exp-1", name="one", model_family="baseline"))
    assert validator.validate_experiment_exists("exp-1", registry).valid is True


@pytest.mark.unit
def test_training_version_registry_paths() -> None:
    registry = TrainingVersionRegistry()
    with pytest.raises(TrainingJobError):
        registry.register(
            version_id="",
            job_id="job-1",
            experiment_id="exp-1",
            semantic_version="1.0.0",
        )
    version = registry.register(
        version_id="v-1",
        job_id="job-1",
        experiment_id="exp-1",
        semantic_version="1.0.0",
    )
    assert registry.get("v-1").version_id == version.version_id
    assert registry.latest_for_job("job-1") is not None
    with pytest.raises(TrainingJobError):
        registry.get("missing")


@pytest.mark.unit
def test_lifecycle_failed_cancelled_and_off_event() -> None:
    lifecycle = TrainingLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_failed(
        job_id="job-1",
        experiment_id="exp-1",
        message="failed",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_cancelled(
        job_id="job-1",
        experiment_id="exp-1",
        correlation_id="c",
        trace_id="t",
    )
    subscription = lifecycle.on_event(lambda _event: None)
    lifecycle.off_event(subscription)
    assert len(lifecycle.events) >= 2


@pytest.mark.unit
def test_runtime_register_experiment_and_build_spec() -> None:
    runtime = make_training_runtime()
    experiment = Experiment.create(
        experiment_id="bridge-exp",
        name="Bridge",
        model_family="baseline",
    )
    runtime.register_experiment(experiment)
    request = runtime.submit_training(
        experiment_id="bridge-exp",
        model_family="baseline",
        dataset_id="dataset-1",
    )
    spec = runtime.build_job_spec(request, job_id="job-bridge")
    assert spec.job_id == "job-bridge"
