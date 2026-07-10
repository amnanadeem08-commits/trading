"""Workflow checkpoint interface and memory implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock

from workflow.exceptions import CheckpointError
from workflow.result import WorkflowResult
from workflow.state import JobState


class CheckpointStore(ABC):
    """Checkpoint persistence contract."""

    @abstractmethod
    def save(
        self,
        workflow_id: str,
        *,
        job_states: dict[str, JobState],
        result: WorkflowResult | None = None,
    ) -> None:
        """Save workflow checkpoint state."""

    @abstractmethod
    def restore(
        self,
        workflow_id: str,
    ) -> tuple[dict[str, JobState], WorkflowResult | None]:
        """Restore workflow checkpoint state."""

    @abstractmethod
    def clear(self, workflow_id: str) -> None:
        """Clear a workflow checkpoint."""


class InMemoryCheckpointStore(CheckpointStore):
    """In-memory checkpoint store for workflow runtime."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._states: dict[str, dict[str, JobState]] = {}
        self._results: dict[str, WorkflowResult | None] = {}

    def save(
        self,
        workflow_id: str,
        *,
        job_states: dict[str, JobState],
        result: WorkflowResult | None = None,
    ) -> None:
        with self._lock:
            self._states[workflow_id] = dict(job_states)
            self._results[workflow_id] = result

    def restore(
        self,
        workflow_id: str,
    ) -> tuple[dict[str, JobState], WorkflowResult | None]:
        with self._lock:
            if workflow_id not in self._states:
                msg = f"No checkpoint found for workflow: {workflow_id}"
                raise CheckpointError(msg)
            return dict(self._states[workflow_id]), self._results.get(workflow_id)

    def clear(self, workflow_id: str) -> None:
        with self._lock:
            self._states.pop(workflow_id, None)
            self._results.pop(workflow_id, None)
