"""Workflow registry."""

from __future__ import annotations

from threading import RLock

from pipeline.registry import PipelineRegistry
from workflow.exceptions import WorkflowNotFoundError, WorkflowRegistrationError
from workflow.validation import WorkflowValidationResult, validate_workflow
from workflow.workflow import Workflow

_default_registry: WorkflowRegistry | None = None
_registry_lock = RLock()


class WorkflowRegistry:
    """Thread-safe registry for workflow definitions."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._workflows: dict[str, Workflow] = {}

    def register(self, workflow: Workflow) -> None:
        """Register a workflow definition."""
        workflow_id = workflow.workflow_id
        if not workflow_id.strip():
            msg = "Workflow id must not be empty"
            raise WorkflowRegistrationError(msg)
        with self._lock:
            if workflow_id in self._workflows:
                msg = f"Workflow already registered: {workflow_id}"
                raise WorkflowRegistrationError(msg)
            self._workflows[workflow_id] = workflow

    def unregister(self, workflow_id: str) -> None:
        with self._lock:
            if workflow_id not in self._workflows:
                raise WorkflowNotFoundError(workflow_id)
            del self._workflows[workflow_id]

    def resolve(self, workflow_id: str) -> Workflow:
        with self._lock:
            workflow = self._workflows.get(workflow_id)
        if workflow is None:
            raise WorkflowNotFoundError(workflow_id)
        return workflow

    def exists(self, workflow_id: str) -> bool:
        with self._lock:
            return workflow_id in self._workflows

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._workflows.keys()))

    def validate(
        self,
        workflow: Workflow,
        pipeline_registry: PipelineRegistry,
    ) -> WorkflowValidationResult:
        """Validate a workflow against registered pipelines."""
        return validate_workflow(workflow, pipeline_registry)


def get_workflow_registry() -> WorkflowRegistry:
    """Return the process-wide default workflow registry."""
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = WorkflowRegistry()
        return _default_registry


def reset_workflow_registry() -> None:
    """Reset the default workflow registry. Intended for tests."""
    global _default_registry
    with _registry_lock:
        _default_registry = None
