"""Workflow runtime coordinator."""

from __future__ import annotations

from config.settings import WorkflowSettings, get_settings
from pipeline.context import PipelineContext, build_pipeline_context
from pipeline.registry import PipelineRegistry, get_pipeline_registry
from pipeline.request import PipelineRequest
from workflow.cancellation import CancellationToken
from workflow.checkpoint import CheckpointStore, InMemoryCheckpointStore
from workflow.exceptions import WorkflowNotFoundError, WorkflowValidationError
from workflow.executor import WorkflowExecutor
from workflow.lifecycle import WorkflowLifecycleEventType
from workflow.queue import InMemoryJobQueue, JobQueue
from workflow.recovery import RecoveryManager
from workflow.registry import WorkflowRegistry, get_workflow_registry
from workflow.result import WorkflowResult
from workflow.scheduler import InMemoryWorkflowScheduler, WorkflowScheduler
from workflow.validation import validate_workflow
from workflow.workflow import Workflow


class WorkflowRuntime:
    """Coordinates workflow loading, execution, stopping, and recovery."""

    def __init__(
        self,
        *,
        workflow_registry: WorkflowRegistry | None = None,
        pipeline_registry: PipelineRegistry | None = None,
        context: PipelineContext | None = None,
        settings: WorkflowSettings | None = None,
        queue: JobQueue | None = None,
        scheduler: WorkflowScheduler | None = None,
        checkpoints: CheckpointStore | None = None,
    ) -> None:
        self._workflow_registry = workflow_registry or get_workflow_registry()
        self._pipeline_registry = pipeline_registry or get_pipeline_registry()
        self._context = context or build_pipeline_context()
        self._settings = settings or get_settings().workflow
        self._queue = queue or InMemoryJobQueue()
        self._scheduler = scheduler or InMemoryWorkflowScheduler()
        self._checkpoints = checkpoints or InMemoryCheckpointStore()
        self._cancellation = CancellationToken()
        self._executor = WorkflowExecutor(
            self._context,
            self._pipeline_registry,
            self._settings,
            checkpoints=self._checkpoints,
        )
        self._recovery = RecoveryManager(
            self._workflow_registry,
            self._executor,
            self._checkpoints,
            self._settings,
        )

    @property
    def workflow_registry(self) -> WorkflowRegistry:
        return self._workflow_registry

    @property
    def pipeline_registry(self) -> PipelineRegistry:
        return self._pipeline_registry

    @property
    def executor(self) -> WorkflowExecutor:
        return self._executor

    @property
    def queue(self) -> JobQueue:
        return self._queue

    @property
    def scheduler(self) -> WorkflowScheduler:
        return self._scheduler

    @property
    def checkpoints(self) -> CheckpointStore:
        return self._checkpoints

    @property
    def recovery(self) -> RecoveryManager:
        return self._recovery

    def load(self, workflow_id: str) -> Workflow:
        """Load a registered workflow definition."""
        if not self._workflow_registry.exists(workflow_id):
            raise WorkflowNotFoundError(workflow_id)
        workflow = self._workflow_registry.resolve(workflow_id)
        validation = validate_workflow(workflow, self._pipeline_registry)
        if not validation.valid:
            msg = "Loaded workflow failed validation"
            raise WorkflowValidationError(msg, errors=validation.errors)
        return workflow

    def execute(self, workflow_id: str, request: PipelineRequest) -> WorkflowResult:
        """Execute a workflow by id."""
        workflow = self.load(workflow_id)
        for job in workflow.jobs:
            self._queue.enqueue(job)
        while self._queue.size() > 0:
            self._queue.dequeue()
        return self._executor.execute(
            workflow,
            request,
            self._context,
            cancellation=self._cancellation,
        )

    def stop(self, workflow_id: str) -> None:
        """Request workflow execution stop."""
        self._cancellation.cancel()
        self._executor.lifecycle.emit(
            WorkflowLifecycleEventType.JOB_CANCELLED,
            workflow_id=workflow_id,
            workflow_version="unknown",
            correlation_id="stop",
            message="workflow stop requested",
        )

    def resume(self, workflow_id: str, request: PipelineRequest) -> WorkflowResult:
        """Resume a workflow from checkpoint."""
        return self._recovery.resume(workflow_id, request, self._context)

    def checkpoint(self, workflow_id: str) -> None:
        """Persist a checkpoint marker for a workflow."""
        if not self._settings.checkpoint_enabled:
            return
        self._checkpoints.save(workflow_id, job_states={})
