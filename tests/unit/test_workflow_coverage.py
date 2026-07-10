"""Additional workflow coverage tests."""

from __future__ import annotations

import pytest

from pipeline import build_pipeline_context, reset_pipeline_registry
from pipeline.registry import PipelineRegistry
from services import reset_application_context
from tests.pipeline_helpers import make_pipeline_request
from tests.workflow_helpers import make_single_job_workflow, setup_ingest_pipeline
from workflow import (
    InMemoryCheckpointStore,
    JobState,
    SequentialParallelExecutor,
    Workflow,
    WorkflowError,
    WorkflowExecutor,
    WorkflowLifecycleEventType,
    WorkflowLifecycleManager,
    WorkflowRegistrationError,
    WorkflowRegistry,
    workflow,
    workflow_metadata,
)
from workflow.exceptions import CircularJobDependencyError, JobNotFoundError


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_pipeline_registry()
    yield
    reset_application_context()
    reset_pipeline_registry()


@pytest.mark.unit
def test_workflow_exceptions_expose_codes() -> None:
    assert WorkflowError("x").code == "workflow_error"
    assert JobNotFoundError("x").code == "job_not_found"
    cycle = CircularJobDependencyError(("a", "b", "a"))
    assert cycle.cycle == ("a", "b", "a")


@pytest.mark.unit
def test_parallel_executor_interface() -> None:
    executor = SequentialParallelExecutor()
    job = make_single_job_workflow().jobs[0]
    assert executor.can_execute_parallel((job,)) is False
    assert executor.max_parallelism() == 1


@workflow(workflow_id="decorated", auto_register=True)
class _DecoratedWorkflow(Workflow):
    workflow_id: str = "decorated-wf"
    version: str = "1.0.0"


@pytest.mark.unit
def test_workflow_metadata_decorator() -> None:
    metadata = workflow_metadata(_DecoratedWorkflow)
    assert metadata["workflow_id"] == "decorated"
    assert metadata["auto_register"] is True


@pytest.mark.unit
def test_lifecycle_off_event() -> None:
    context = build_pipeline_context()
    lifecycle = WorkflowLifecycleManager(context)
    seen: list[str] = []
    subscription = lifecycle.on_event(lambda event: seen.append(event.event_type.value))
    lifecycle.off_event(subscription)
    lifecycle.emit(
        WorkflowLifecycleEventType.WORKFLOW_STARTED,
        workflow_id="wf",
        workflow_version="1.0.0",
        correlation_id="corr",
        message="started",
    )
    assert seen == []


@pytest.mark.unit
def test_registry_duplicate_raises() -> None:
    registry = WorkflowRegistry()
    workflow = make_single_job_workflow()
    registry.register(workflow)
    with pytest.raises(WorkflowRegistrationError):
        registry.register(workflow)


@pytest.mark.unit
def test_executor_resume_with_checkpoint_states() -> None:
    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    context = build_pipeline_context()
    checkpoints = InMemoryCheckpointStore()
    checkpoints.save(
        "wf-single",
        job_states={"job-ingest": JobState.COMPLETED},
    )
    executor = WorkflowExecutor(
        context,
        pipeline_registry,
        context.settings.workflow,
        checkpoints=checkpoints,
    )
    result = executor.execute(
        make_single_job_workflow(),
        make_pipeline_request(),
        context,
        initial_job_states={"job-ingest": JobState.COMPLETED},
    )
    assert result.status.value == "completed"


@pytest.mark.unit
def test_recovery_resume_executes_workflow() -> None:
    from config.settings import WorkflowSettings
    from workflow import RecoveryManager, WorkflowRegistry, reset_workflow_registry

    reset_workflow_registry()
    pipeline_registry = PipelineRegistry()
    workflow_registry = WorkflowRegistry()
    setup_ingest_pipeline(pipeline_registry)
    workflow_registry.register(make_single_job_workflow())
    context = build_pipeline_context()
    checkpoints = InMemoryCheckpointStore()
    checkpoints.save("wf-single", job_states={"job-ingest": JobState.COMPLETED})
    settings = WorkflowSettings(recovery_enabled=True, checkpoint_enabled=True)
    executor = WorkflowExecutor(context, pipeline_registry, settings, checkpoints=checkpoints)
    recovery = RecoveryManager(workflow_registry, executor, checkpoints, settings)
    result = recovery.resume("wf-single", make_pipeline_request(), context)
    assert result.status.value == "completed"


@pytest.mark.unit
def test_recovery_resume_disabled_raises() -> None:
    from config.settings import WorkflowSettings
    from workflow import RecoveryManager, WorkflowRegistry, WorkflowValidationError

    pipeline_registry = PipelineRegistry()
    workflow_registry = WorkflowRegistry()
    setup_ingest_pipeline(pipeline_registry)
    workflow_registry.register(make_single_job_workflow())
    context = build_pipeline_context()
    settings = WorkflowSettings(recovery_enabled=False)
    executor = WorkflowExecutor(context, pipeline_registry, settings)
    recovery = RecoveryManager(workflow_registry, executor, InMemoryCheckpointStore(), settings)
    with pytest.raises(WorkflowValidationError):
        recovery.resume("wf-single", make_pipeline_request(), context)


@pytest.mark.unit
def test_runtime_stop_and_checkpoint() -> None:
    from workflow import WorkflowRuntime

    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    runtime = WorkflowRuntime(pipeline_registry=pipeline_registry)
    runtime.workflow_registry.register(make_single_job_workflow())
    runtime.checkpoint("wf-single")
    runtime.stop("wf-single")
    states, _ = runtime.checkpoints.restore("wf-single")
    assert states == {}


@pytest.mark.unit
def test_registry_validate_method() -> None:
    pipeline_registry = PipelineRegistry()
    workflow_registry = WorkflowRegistry()
    setup_ingest_pipeline(pipeline_registry)
    workflow = make_single_job_workflow()
    result = workflow_registry.validate(workflow, pipeline_registry)
    assert result.valid is True


@pytest.mark.unit
def test_validate_duplicate_job_ids() -> None:
    from pipeline.registry import PipelineRegistry
    from workflow import Job, Workflow, validate_workflow

    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    workflow = Workflow(
        workflow_id="dup",
        version="1.0.0",
        jobs=(
            Job(job_id="same", pipeline_name="ingest-pipeline"),
            Job(job_id="same", pipeline_name="ingest-pipeline"),
        ),
    )
    result = validate_workflow(workflow, pipeline_registry)
    assert result.valid is False
    assert any("Duplicate" in error for error in result.errors)


@pytest.mark.unit
def test_job_timeout_error_code() -> None:
    from workflow.exceptions import InvalidJobStateError, JobTimeoutError, WorkflowRegistrationError

    assert JobTimeoutError("job-1", 30).code == "job_timeout"
    assert InvalidJobStateError("job-1", "running", "stop").code == "invalid_job_state"
    assert WorkflowRegistrationError("dup").code == "workflow_registration_error"
