"""Additional pipeline coverage tests."""

from __future__ import annotations

import pytest

from pipeline import (
    PipelineBuilder,
    PipelineExecutor,
    PipelineLifecycleManager,
    PipelineNotFoundError,
    PipelineRegistrationError,
    PipelineRegistry,
    StageNotFoundError,
    build_pipeline_context,
    stage_metadata,
)
from pipeline.exceptions import CircularStageDependencyError, PipelineError
from pipeline.lifecycle import PipelineLifecycleEventType
from services import reset_application_context
from tests.pipeline_fixtures import IngestStage, PublishStage
from tests.pipeline_helpers import make_pipeline_request


@pytest.fixture(autouse=True)
def _reset_context() -> None:
    reset_application_context()
    yield
    reset_application_context()


@pytest.mark.unit
def test_pipeline_exceptions_expose_codes() -> None:
    assert PipelineError("x").code == "pipeline_error"
    assert PipelineNotFoundError("x").code == "pipeline_not_found"
    assert StageNotFoundError("x").code == "stage_not_found"
    cycle = CircularStageDependencyError(("a", "b", "a"))
    assert cycle.cycle == ("a", "b", "a")


@pytest.mark.unit
def test_registry_register_stage_and_duplicate_pipeline() -> None:
    registry = PipelineRegistry()
    registry.register_stage(IngestStage)
    assert "ingest" in registry.list_stages()
    pipeline = PipelineBuilder("dup").add_stage(IngestStage()).build()
    registry.register_pipeline(pipeline)
    with pytest.raises(PipelineRegistrationError):
        registry.register_pipeline(pipeline)


@pytest.mark.unit
def test_registry_unregister_stage_missing() -> None:
    registry = PipelineRegistry()
    with pytest.raises(StageNotFoundError):
        registry.unregister_stage("missing")


@pytest.mark.unit
def test_stage_metadata_decorator() -> None:
    metadata = stage_metadata(PublishStage)
    assert metadata["name"] == "publish"
    assert metadata["auto_register"] is True


@pytest.mark.unit
def test_lifecycle_off_event() -> None:
    context = build_pipeline_context()
    lifecycle = PipelineLifecycleManager(context)
    seen: list[str] = []
    subscription = lifecycle.on_event(lambda event: seen.append(event.event_type.value))
    lifecycle.off_event(subscription)
    lifecycle.emit(
        PipelineLifecycleEventType.PIPELINE_STARTED,
        pipeline_name="p",
        pipeline_version="1.0.0",
        request=make_pipeline_request(),
        message="started",
    )
    assert seen == []


@pytest.mark.unit
def test_executor_stage_validation_failure() -> None:
    context = build_pipeline_context()
    stage = IngestStage()
    stage._fail_validate = True
    pipeline = PipelineBuilder("validate-fail").add_stage(stage).build()
    response = PipelineExecutor(context).execute(pipeline, make_pipeline_request())
    assert response.result.status.value == "failed"
