"""Workflow job executor."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from config.settings import WorkflowSettings
from health.models import HealthState
from models.common import VersionInfo, utc_now
from pipeline.context import PipelineContext
from pipeline.executor import PipelineExecutor
from pipeline.registry import PipelineRegistry
from pipeline.request import PipelineRequest
from workflow.cancellation import CancellationToken
from workflow.checkpoint import CheckpointStore
from workflow.exceptions import (
    JobExecutionError,
    JobTimeoutError,
    WorkflowCancelledError,
    WorkflowValidationError,
)
from workflow.job import Job
from workflow.lifecycle import WorkflowLifecycleEventType, WorkflowLifecycleManager
from workflow.result import JobResult, WorkflowResult
from workflow.state import JobState, WorkflowStatus
from workflow.validation import validate_workflow
from workflow.workflow import Workflow


class ParallelExecutor(ABC):
    """Interface for parallel-ready job execution. No implementation in foundation."""

    @abstractmethod
    def can_execute_parallel(self, jobs: tuple[Job, ...]) -> bool:
        """Return whether the provided jobs can execute in parallel."""

    @abstractmethod
    def max_parallelism(self) -> int:
        """Return maximum supported parallel job count."""


class SequentialParallelExecutor(ParallelExecutor):
    """Default sequential executor exposing parallel-ready interface."""

    def can_execute_parallel(self, jobs: tuple[Job, ...]) -> bool:
        return len(jobs) > 1

    def max_parallelism(self) -> int:
        return 1


class WorkflowExecutor:
    """Executes workflow jobs with dependency ordering and observability."""

    def __init__(
        self,
        context: PipelineContext,
        pipeline_registry: PipelineRegistry,
        settings: WorkflowSettings,
        *,
        checkpoints: CheckpointStore | None = None,
        parallel_executor: ParallelExecutor | None = None,
    ) -> None:
        self._context = context
        self._pipeline_registry = pipeline_registry
        self._pipeline_executor = PipelineExecutor(context)
        self._settings = settings
        self._checkpoints = checkpoints
        self._parallel_executor = parallel_executor or SequentialParallelExecutor()
        self._lifecycle = WorkflowLifecycleManager(context)

    @property
    def lifecycle(self) -> WorkflowLifecycleManager:
        return self._lifecycle

    @property
    def parallel_executor(self) -> ParallelExecutor:
        return self._parallel_executor

    def execute(
        self,
        workflow: Workflow,
        request: PipelineRequest,
        context: PipelineContext,
        *,
        cancellation: CancellationToken | None = None,
        initial_job_states: dict[str, JobState] | None = None,
    ) -> WorkflowResult:
        """Execute all jobs in a workflow."""
        token = cancellation or CancellationToken()
        validation = validate_workflow(workflow, self._pipeline_registry)
        if not validation.valid:
            msg = "Workflow validation failed"
            raise WorkflowValidationError(msg, errors=validation.errors)

        job_states: dict[str, JobState] = {job.job_id: JobState.CREATED for job in workflow.jobs}
        if initial_job_states is not None:
            job_states.update(initial_job_states)

        completed_jobs: list[str] = []
        failed_jobs: list[str] = []
        cancelled_jobs: list[str] = []
        job_results: list[JobResult] = []
        timings: dict[str, float] = {}
        metrics: dict[str, object] = {}
        workflow_started = time.perf_counter()

        self._register_workflow_observability(workflow)
        self._lifecycle.emit(
            WorkflowLifecycleEventType.WORKFLOW_STARTED,
            workflow_id=workflow.workflow_id,
            workflow_version=workflow.version,
            correlation_id=request.correlation_id,
            message="workflow started",
        )

        try:
            for job_id in validation.execution_order:
                self._check_cancellation(workflow, token)
                job = self._job_by_id(workflow, job_id)
                if not self._dependencies_satisfied(job, job_states):
                    job_states[job_id] = JobState.WAITING
                    continue
                if job_states.get(job_id) == JobState.COMPLETED:
                    completed_jobs.append(job_id)
                    continue

                job_states[job_id] = JobState.QUEUED
                job_states[job_id] = JobState.RUNNING
                self._register_job_observability(job)
                self._lifecycle.emit(
                    WorkflowLifecycleEventType.JOB_STARTED,
                    workflow_id=workflow.workflow_id,
                    workflow_version=workflow.version,
                    correlation_id=request.correlation_id,
                    job_id=job_id,
                    message="job started",
                )

                job_started = time.perf_counter()
                try:
                    pipeline = self._pipeline_registry.resolve(job.pipeline_name)
                    pipeline_response = self._pipeline_executor.execute(pipeline, request)
                    duration_ms = (time.perf_counter() - job_started) * 1000.0
                    if duration_ms > job.timeout_seconds * 1000.0:
                        raise JobTimeoutError(job_id, job.timeout_seconds)
                    if pipeline_response.result.status.value == "failed":
                        raise JobExecutionError(
                            job_id,
                            (
                                pipeline_response.result.errors[0]
                                if pipeline_response.result.errors
                                else "pipeline failed"
                            ),
                        )
                    job_states[job_id] = JobState.COMPLETED
                    completed_jobs.append(job_id)
                    timings[job_id] = duration_ms
                    self._context.metrics.counter(f"workflow.job.{job_id}.success").inc(1)
                    job_result = JobResult(
                        job_id=job_id,
                        pipeline_name=job.pipeline_name,
                        state=JobState.COMPLETED,
                        message="completed",
                        duration_ms=duration_ms,
                        pipeline_response=pipeline_response,
                        completed_at=utc_now(),
                    )
                    job_results.append(job_result)
                    self._lifecycle.emit(
                        WorkflowLifecycleEventType.JOB_COMPLETED,
                        workflow_id=workflow.workflow_id,
                        workflow_version=workflow.version,
                        correlation_id=request.correlation_id,
                        job_id=job_id,
                        message="job completed",
                    )
                except WorkflowCancelledError:
                    raise
                except Exception as error:
                    duration_ms = (time.perf_counter() - job_started) * 1000.0
                    job_states[job_id] = JobState.FAILED
                    failed_jobs.append(job_id)
                    timings[job_id] = duration_ms
                    self._context.metrics.counter(f"workflow.job.{job_id}.failure").inc(1)
                    job_results.append(
                        JobResult(
                            job_id=job_id,
                            pipeline_name=job.pipeline_name,
                            state=JobState.FAILED,
                            message=str(error),
                            duration_ms=duration_ms,
                            completed_at=utc_now(),
                        )
                    )
                    self._lifecycle.emit(
                        WorkflowLifecycleEventType.JOB_FAILED,
                        workflow_id=workflow.workflow_id,
                        workflow_version=workflow.version,
                        correlation_id=request.correlation_id,
                        job_id=job_id,
                        message=str(error),
                    )
                    return self._finalize_result(
                        workflow,
                        WorkflowStatus.FAILED,
                        completed_jobs,
                        failed_jobs,
                        cancelled_jobs,
                        job_results,
                        metrics,
                        timings,
                        workflow_started,
                        request,
                        event_type=WorkflowLifecycleEventType.WORKFLOW_FAILED,
                    )

                if self._checkpoints is not None and self._settings.checkpoint_enabled:
                    self._checkpoints.save(
                        workflow.workflow_id,
                        job_states=job_states,
                    )

            status = WorkflowStatus.CANCELLED if token.is_cancelled() else WorkflowStatus.COMPLETED
            return self._finalize_result(
                workflow,
                status,
                completed_jobs,
                failed_jobs,
                cancelled_jobs,
                job_results,
                metrics,
                timings,
                workflow_started,
                request,
                event_type=(
                    WorkflowLifecycleEventType.WORKFLOW_FAILED
                    if status == WorkflowStatus.CANCELLED
                    else WorkflowLifecycleEventType.WORKFLOW_COMPLETED
                ),
            )
        except WorkflowCancelledError as error:
            for job in workflow.jobs:
                if job_states.get(job.job_id) == JobState.RUNNING:
                    job_states[job.job_id] = JobState.CANCELLED
                    cancelled_jobs.append(job.job_id)
            return self._finalize_result(
                workflow,
                WorkflowStatus.CANCELLED,
                completed_jobs,
                failed_jobs,
                cancelled_jobs,
                job_results,
                metrics,
                timings,
                workflow_started,
                request,
                message=str(error),
                event_type=WorkflowLifecycleEventType.WORKFLOW_FAILED,
            )

    def _finalize_result(
        self,
        workflow: Workflow,
        status: WorkflowStatus,
        completed_jobs: list[str],
        failed_jobs: list[str],
        cancelled_jobs: list[str],
        job_results: list[JobResult],
        metrics: dict[str, object],
        timings: dict[str, float],
        workflow_started: float,
        request: PipelineRequest,
        *,
        message: str | None = None,
        event_type: WorkflowLifecycleEventType,
    ) -> WorkflowResult:
        total_ms = (time.perf_counter() - workflow_started) * 1000.0
        metrics["workflow.total_duration_ms"] = total_ms
        metrics["workflow.job_count"] = len(job_results)
        metrics["workflow.parallel_ready"] = self._parallel_executor.can_execute_parallel(
            workflow.jobs
        )
        result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            status=status,
            completed_jobs=tuple(completed_jobs),
            failed_jobs=tuple(failed_jobs),
            cancelled_jobs=tuple(cancelled_jobs),
            job_results=tuple(job_results),
            metrics=metrics,
            timings=timings,
            completed_at=utc_now(),
        )
        self._lifecycle.emit(
            event_type,
            workflow_id=workflow.workflow_id,
            workflow_version=workflow.version,
            correlation_id=request.correlation_id,
            message=message or status.value,
        )
        if self._checkpoints is not None and self._settings.checkpoint_enabled:
            self._checkpoints.save(
                workflow.workflow_id,
                job_states={job_result.job_id: job_result.state for job_result in job_results},
                result=result,
            )
        return result

    def _dependencies_satisfied(self, job: Job, job_states: dict[str, JobState]) -> bool:
        return all(job_states.get(dep) == JobState.COMPLETED for dep in job.dependencies)

    def _job_by_id(self, workflow: Workflow, job_id: str) -> Job:
        for job in workflow.jobs:
            if job.job_id == job_id:
                return job
        msg = f"Job not found: {job_id}"
        raise WorkflowValidationError(msg)

    def _check_cancellation(self, workflow: Workflow, token: CancellationToken) -> None:
        if token.is_cancelled():
            raise WorkflowCancelledError(workflow.workflow_id)

    def _register_workflow_observability(self, workflow: Workflow) -> None:
        self._context.health.register(
            f"workflow.{workflow.workflow_id}",
            lambda: (HealthState.HEALTHY, "workflow ready"),
        )
        self._context.metrics.gauge(f"workflow.{workflow.workflow_id}.ready").set(1.0)
        self._context.application.logger_factory.create(
            service_name=f"workflow.{workflow.workflow_id}"
        )
        version_id = workflow.version
        if not self._context.version_registry.services.exists(version_id):
            self._context.version_registry.services.register(
                VersionInfo(version_id=version_id, description=workflow.workflow_id),
            )

    def _register_job_observability(self, job: Job) -> None:
        self._context.health.register(
            f"workflow.job.{job.job_id}",
            lambda: (HealthState.HEALTHY, "job ready"),
            dependencies=job.dependencies,
        )
        self._context.metrics.gauge(f"workflow.job.{job.job_id}.ready").set(1.0)
