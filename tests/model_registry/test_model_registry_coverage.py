"""Extended unit tests for model registry coverage."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from model_registry import (
    ExperimentRun,
    LineageError,
    LineageGraph,
    LineageNodeType,
    ModelRegistrationError,
    ModelRegistry,
    ModelRegistryError,
    ModelStage,
    ModelStatus,
    PromotionError,
    RegistryLifecycleEventType,
    RegistryLifecycleManager,
    RegistryValidationError,
    RegistryValidator,
    RegistryVersionRegistry,
)
from model_registry.experiments.experiment_metrics import ExperimentMetrics
from tests.model_registry_helpers import make_registered_model, seed_trained_model


@pytest.mark.unit
def test_model_stage_transitions() -> None:
    assert ModelStage.DRAFT.next_stage() == ModelStage.STAGING
    assert ModelStage.PRODUCTION.is_terminal() is True
    assert ModelStage.ARCHIVED.is_terminal() is True


@pytest.mark.unit
def test_model_status_availability() -> None:
    assert ModelStatus.ACTIVE.is_available() is True
    assert ModelStatus.DISABLED.is_available() is False


@pytest.mark.unit
def test_experiment_metrics_get() -> None:
    metrics = ExperimentMetrics(
        run_id="run-1",
        experiment_id="exp-1",
        values={"score": 0.9},
    )
    assert metrics.get("score") == 0.9
    assert metrics.get("missing", 1.0) == 1.0


@pytest.mark.unit
def test_registry_version_registry_paths() -> None:
    registry = RegistryVersionRegistry()
    with pytest.raises(ModelRegistryError):
        registry.register(version_id="", registry_schema="1.0.0")
    version = registry.register(version_id="v1", registry_schema="1.0.0")
    assert registry.get("v1").version_id == version.version_id
    assert registry.latest() is not None
    assert len(registry.list_versions()) == 1
    with pytest.raises(ModelRegistryError):
        registry.get("missing")


@pytest.mark.unit
def test_promotion_registry_approval_paths() -> None:
    runtime = seed_trained_model(approval_required=False)
    version = runtime.registry.latest("model-1")
    request = runtime.registry.promotion_registry.create_approval_request(
        model_id="model-1",
        version_id=version.version_id,
        from_stage=ModelStage.DRAFT,
        to_stage=ModelStage.STAGING,
    )
    result = runtime.registry.promotion_registry.resolve_approval(
        request,
        approved=True,
        message="ok",
    )
    assert result.approved is True
    assert runtime.registry.promotion_registry.get_approval_request(request.request_id)
    assert len(runtime.registry.promotion_registry.list_approval_requests()) == 1
    resolved = runtime.registry.promotion_registry.get_approval_request(request.request_id)
    with pytest.raises(PromotionError):
        runtime.registry.promotion_registry.resolve_approval(resolved, approved=False)
    with pytest.raises(PromotionError):
        runtime.registry.promotion_registry.get_approval_request("missing")


@pytest.mark.unit
def test_model_registry_archive_and_limits() -> None:
    registry = ModelRegistry(max_versions_per_model=1)
    registry.register_model(make_registered_model())
    version = registry.build_version(
        model_id="model-1",
        semantic_version="1.0.0",
        artifact_id="artifact-1",
        dataset_id="dataset-1",
        experiment_id="exp-1",
        run_id="run-1",
        job_id="job-1",
        config_hash="hash",
        checksum="checksum-1",
    )
    registry.register_version(version)
    archived = registry.archive("model-1")
    assert archived.status == ModelStatus.DEPRECATED
    with pytest.raises(ModelRegistrationError):
        registry.register_version(
            version.model_copy(
                update={"version_id": registry.new_version_id(), "checksum": "checksum-2"}
            )
        )


@pytest.mark.unit
def test_lineage_graph_edge_errors() -> None:
    graph = LineageGraph()
    graph.add_node(
        node_id="dataset:ds-1",
        node_type=LineageNodeType.DATASET,
        label="ds-1",
        reference_id="ds-1",
    )
    with pytest.raises(LineageError):
        graph.add_edge(source_id="dataset:ds-1", target_id="missing", relation="trained_on")
    with pytest.raises(LineageError):
        graph.descendants("missing")


@pytest.mark.unit
def test_runtime_snapshot_and_artifact_run() -> None:
    runtime = seed_trained_model()
    artifact = runtime.training_runtime.artifact_store.get(
        runtime.registry.latest("model-1").artifact_id
    )
    run = runtime.experiment_run_from_artifact(artifact)
    snapshot = runtime.capture_experiment_snapshot(run)
    assert snapshot.immutable is True
    assert isinstance(run, ExperimentRun)


@pytest.mark.unit
def test_registry_lifecycle_additional_events() -> None:
    lifecycle = RegistryLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_model_archived(
        model_id="model-1",
        correlation_id="c",
        trace_id="t",
    )
    lifecycle.emit_lineage_updated(
        model_id="model-1",
        version_id="version-1",
        correlation_id="c",
        trace_id="t",
    )
    subscription = lifecycle.on_event(lambda _event: None)
    lifecycle.off_event(subscription)
    types = {event.event_type for event in lifecycle.events}
    assert RegistryLifecycleEventType.MODEL_ARCHIVED in types
    assert RegistryLifecycleEventType.LINEAGE_UPDATED in types


@pytest.mark.unit
def test_ingest_training_result_rejects_incomplete() -> None:
    from training_pipeline import TrainingJobStatus
    from training_pipeline.jobs.training_result import TrainingResult

    runtime = seed_trained_model()
    failed = TrainingResult(
        job_id="job-fail",
        experiment_id="exp-1",
        run_id="run-fail",
        status=TrainingJobStatus.FAILED,
        message="failed",
    )
    with pytest.raises(ModelRegistryError):
        runtime.ingest_training_result(
            model_id="model-1",
            training_result=failed,
            experiment_id="exp-1",
        )


@pytest.mark.unit
def test_validator_ensure_valid_raises() -> None:
    validator = RegistryValidator()
    result = validator.validate_model(make_registered_model(model_id=""))
    with pytest.raises(RegistryValidationError):
        validator.ensure_valid(result)


@pytest.mark.unit
def test_validator_version_field_errors() -> None:
    validator = RegistryValidator()
    registry = ModelRegistry()
    registry.register_model(make_registered_model())
    version = registry.build_version(
        model_id="model-1",
        semantic_version="1.0.0",
        artifact_id="",
        dataset_id="",
        experiment_id="exp-1",
        run_id="run-1",
        job_id="job-1",
        config_hash="",
        checksum="",
    )
    result = validator.validate_version(version)
    assert result.valid is False
    assert len(result.errors) >= 3


@pytest.mark.unit
def test_catalog_empty_versions() -> None:
    runtime = seed_trained_model()
    entry = runtime.registry.catalog.get("model-1")
    assert entry is not None
    assert runtime.registry.catalog.list_versions("missing") == ()
