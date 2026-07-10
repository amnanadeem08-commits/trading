"""Unit tests for workflow registry and validation."""

from __future__ import annotations

import pytest

from pipeline import reset_pipeline_registry
from pipeline.registry import PipelineRegistry
from services import reset_application_context
from tests.workflow_helpers import (
    make_dependent_workflow,
    make_single_job_workflow,
    setup_ingest_pipeline,
    setup_transform_pipeline,
)
from workflow import (
    CircularJobDependencyError,
    Job,
    Workflow,
    WorkflowNotFoundError,
    WorkflowRegistry,
    get_workflow_registry,
    reset_workflow_registry,
    validate_workflow,
)


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_pipeline_registry()
    reset_workflow_registry()
    yield
    reset_application_context()
    reset_pipeline_registry()
    reset_workflow_registry()


@pytest.mark.unit
def test_registry_register_resolve_list() -> None:
    registry = WorkflowRegistry()
    workflow = make_single_job_workflow()
    registry.register(workflow)
    assert registry.exists("wf-single") is True
    assert registry.resolve("wf-single").workflow_id == "wf-single"
    assert registry.list() == ("wf-single",)


@pytest.mark.unit
def test_validate_missing_pipeline() -> None:
    pipeline_registry = PipelineRegistry()
    result = validate_workflow(make_single_job_workflow(), pipeline_registry)
    assert result.valid is False
    assert any("Pipeline not registered" in error for error in result.errors)


@pytest.mark.unit
def test_validate_execution_order() -> None:
    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    setup_transform_pipeline(pipeline_registry)
    result = validate_workflow(make_dependent_workflow(), pipeline_registry)
    assert result.valid is True
    assert result.execution_order == ("job-ingest", "job-transform")


@pytest.mark.unit
def test_validate_cycle_raises() -> None:
    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    workflow = Workflow(
        workflow_id="wf-cycle",
        version="1.0.0",
        jobs=(
            Job(job_id="a", pipeline_name="ingest-pipeline", dependencies=("c",)),
            Job(job_id="b", pipeline_name="ingest-pipeline", dependencies=("a",)),
            Job(job_id="c", pipeline_name="ingest-pipeline", dependencies=("b",)),
        ),
    )
    with pytest.raises(CircularJobDependencyError):
        validate_workflow(workflow, pipeline_registry)


@pytest.mark.unit
def test_registry_unregister_missing() -> None:
    registry = WorkflowRegistry()
    with pytest.raises(WorkflowNotFoundError):
        registry.unregister("missing")


@pytest.mark.unit
def test_get_workflow_registry_singleton() -> None:
    assert get_workflow_registry() is get_workflow_registry()
