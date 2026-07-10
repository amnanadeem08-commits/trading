"""Unit tests for workflow checkpoint and recovery."""

from __future__ import annotations

import pytest

from config.settings import WorkflowSettings
from pipeline import build_pipeline_context, reset_pipeline_registry
from pipeline.registry import PipelineRegistry
from services import reset_application_context
from tests.pipeline_helpers import make_pipeline_request
from tests.workflow_helpers import (
    make_single_job_workflow,
    register_workflow,
    setup_ingest_pipeline,
)
from workflow import (
    CheckpointError,
    InMemoryCheckpointStore,
    JobState,
    RecoveryManager,
    WorkflowExecutor,
    WorkflowRegistry,
    WorkflowRuntime,
    WorkflowStatus,
)


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_pipeline_registry()
    yield
    reset_application_context()
    reset_pipeline_registry()


@pytest.mark.unit
def test_checkpoint_save_restore_clear() -> None:
    store = InMemoryCheckpointStore()
    store.save("wf-1", job_states={"job-a": JobState.COMPLETED})
    states, result = store.restore("wf-1")
    assert states["job-a"] == JobState.COMPLETED
    assert result is None
    store.clear("wf-1")
    with pytest.raises(CheckpointError):
        store.restore("wf-1")


@pytest.mark.unit
def test_recovery_restart_executes_workflow() -> None:
    pipeline_registry = PipelineRegistry()
    workflow_registry = WorkflowRegistry()
    setup_ingest_pipeline(pipeline_registry)
    workflow = make_single_job_workflow()
    register_workflow(workflow_registry, workflow)
    runtime = WorkflowRuntime(
        workflow_registry=workflow_registry,
        pipeline_registry=pipeline_registry,
    )
    request = make_pipeline_request()
    result = runtime.recovery.restart("wf-single", request, build_pipeline_context())
    assert result.status == WorkflowStatus.COMPLETED
    assert result.completed_jobs == ("job-ingest",)


@pytest.mark.unit
def test_recovery_rollback_cancels_jobs() -> None:
    pipeline_registry = PipelineRegistry()
    workflow_registry = WorkflowRegistry()
    setup_ingest_pipeline(pipeline_registry)
    workflow = make_single_job_workflow()
    workflow_registry.register(workflow)
    settings = WorkflowSettings(recovery_enabled=True, checkpoint_enabled=True)
    checkpoints = InMemoryCheckpointStore()
    executor = WorkflowExecutor(
        build_pipeline_context(),
        pipeline_registry,
        settings,
        checkpoints=checkpoints,
    )
    recovery = RecoveryManager(
        workflow_registry,
        executor,
        checkpoints,
        settings,
    )
    result = recovery.rollback("wf-single", make_pipeline_request(), build_pipeline_context())
    assert result.status == WorkflowStatus.CANCELLED
    assert "job-ingest" in result.cancelled_jobs
