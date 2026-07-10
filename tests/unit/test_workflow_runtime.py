"""Unit tests for workflow runtime and executor."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from pipeline import build_pipeline_context, reset_pipeline_registry
from pipeline.registry import PipelineRegistry
from services import reset_application_context
from services.context import ApplicationContext
from tests.pipeline_helpers import make_pipeline_request
from tests.workflow_helpers import (
    make_dependent_workflow,
    make_single_job_workflow,
    setup_ingest_pipeline,
    setup_transform_pipeline,
)
from workflow import (
    CancellationToken,
    WorkflowExecutor,
    WorkflowLifecycleEventType,
    WorkflowNotFoundError,
    WorkflowRuntime,
    WorkflowStatus,
    reset_workflow_registry,
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
def test_runtime_executes_single_job_workflow() -> None:
    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    runtime = WorkflowRuntime(pipeline_registry=pipeline_registry)
    workflow = make_single_job_workflow()
    runtime.workflow_registry.register(workflow)
    result = runtime.execute("wf-single", make_pipeline_request())
    assert result.status == WorkflowStatus.COMPLETED
    assert result.completed_jobs == ("job-ingest",)


@pytest.mark.unit
def test_runtime_executes_dependent_jobs_in_order() -> None:
    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    setup_transform_pipeline(pipeline_registry)
    runtime = WorkflowRuntime(pipeline_registry=pipeline_registry)
    runtime.workflow_registry.register(make_dependent_workflow())
    result = runtime.execute("wf-chain", make_pipeline_request())
    assert result.status == WorkflowStatus.COMPLETED
    assert result.completed_jobs == ("job-ingest", "job-transform")


@pytest.mark.unit
def test_executor_emits_lifecycle_events_to_event_bus() -> None:
    bus = EventBus()
    application = build_pipeline_context().application
    updated_app = ApplicationContext(
        settings=application.settings,
        feature_flags=application.feature_flags,
        event_bus=bus,
        metrics=application.metrics,
        health=application.health,
        audit=application.audit,
        version_registry=application.version_registry,
        logger_factory=application.logger_factory,
        configuration_hash=application.configuration_hash,
    )
    from pipeline.context import PipelineContext

    context = PipelineContext(settings=updated_app.settings, application=updated_app)
    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    runtime = WorkflowRuntime(pipeline_registry=pipeline_registry, context=context)
    runtime.workflow_registry.register(make_single_job_workflow())
    runtime.execute("wf-single", make_pipeline_request())
    assert bus.persistence.count() >= 1


@pytest.mark.unit
def test_executor_cancellation() -> None:
    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    context = build_pipeline_context()
    executor = WorkflowExecutor(context, pipeline_registry, context.settings.workflow)
    token = CancellationToken()
    token.cancel()
    workflow = make_single_job_workflow()
    result = executor.execute(
        workflow,
        make_pipeline_request(),
        context,
        cancellation=token,
    )
    assert result.status == WorkflowStatus.CANCELLED


@pytest.mark.unit
def test_runtime_load_missing_raises() -> None:
    runtime = WorkflowRuntime()
    with pytest.raises(WorkflowNotFoundError):
        runtime.load("missing")


@pytest.mark.unit
def test_executor_lifecycle_event_types() -> None:
    pipeline_registry = PipelineRegistry()
    setup_ingest_pipeline(pipeline_registry)
    context = build_pipeline_context()
    executor = WorkflowExecutor(context, pipeline_registry, context.settings.workflow)
    workflow = make_single_job_workflow()
    executor.execute(workflow, make_pipeline_request(), context)
    event_types = {event.event_type for event in executor.lifecycle.events}
    assert WorkflowLifecycleEventType.WORKFLOW_STARTED in event_types
    assert WorkflowLifecycleEventType.JOB_STARTED in event_types
    assert WorkflowLifecycleEventType.WORKFLOW_COMPLETED in event_types
