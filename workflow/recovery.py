"""Workflow recovery manager scaffold."""

from __future__ import annotations

from contextlib import suppress

from config.settings import WorkflowSettings
from pipeline.context import PipelineContext
from pipeline.request import PipelineRequest
from workflow.checkpoint import CheckpointStore
from workflow.exceptions import CheckpointError, WorkflowValidationError
from workflow.executor import WorkflowExecutor
from workflow.lifecycle import WorkflowLifecycleEventType
from workflow.registry import WorkflowRegistry
from workflow.result import WorkflowResult
from workflow.state import WorkflowStatus


class RecoveryManager:
    """Coordinates workflow resume, restart, and rollback operations."""

    def __init__(
        self,
        registry: WorkflowRegistry,
        executor: WorkflowExecutor,
        checkpoints: CheckpointStore,
        settings: WorkflowSettings,
    ) -> None:
        self._registry = registry
        self._executor = executor
        self._checkpoints = checkpoints
        self._settings = settings

    def resume(
        self,
        workflow_id: str,
        request: PipelineRequest,
        context: PipelineContext,
    ) -> WorkflowResult:
        """Resume a workflow from the latest checkpoint."""
        if not self._settings.recovery_enabled:
            msg = "Workflow recovery is disabled"
            raise WorkflowValidationError(msg)
        workflow = self._registry.resolve(workflow_id)
        job_states, _ = self._checkpoints.restore(workflow_id)
        self._executor.lifecycle.emit(
            WorkflowLifecycleEventType.WORKFLOW_STARTED,
            workflow_id=workflow.workflow_id,
            workflow_version=workflow.version,
            correlation_id=request.correlation_id,
            message="workflow resumed",
        )
        return self._executor.execute(
            workflow,
            request,
            context,
            initial_job_states=job_states,
        )

    def restart(
        self,
        workflow_id: str,
        request: PipelineRequest,
        context: PipelineContext,
    ) -> WorkflowResult:
        """Restart a workflow from the beginning."""
        self._checkpoints.clear(workflow_id)
        workflow = self._registry.resolve(workflow_id)
        return self._executor.execute(workflow, request, context)

    def rollback(
        self,
        workflow_id: str,
        request: PipelineRequest,
        context: PipelineContext,
    ) -> WorkflowResult:
        """Rollback workflow state and clear checkpoints."""
        with suppress(CheckpointError):
            self._checkpoints.clear(workflow_id)
        workflow = self._registry.resolve(workflow_id)
        result = WorkflowResult(
            workflow_id=workflow.workflow_id,
            status=WorkflowStatus.CANCELLED,
            cancelled_jobs=tuple(job.job_id for job in workflow.jobs),
            metrics={"rollback": True},
        )
        self._executor.lifecycle.emit(
            WorkflowLifecycleEventType.WORKFLOW_FAILED,
            workflow_id=workflow.workflow_id,
            workflow_version=workflow.version,
            correlation_id=request.correlation_id,
            message="workflow rolled back",
        )
        return result
