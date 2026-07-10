"""Workflow scheduler scaffold."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from threading import RLock
from uuid import uuid4

from workflow.workflow import Workflow


@dataclass(frozen=True)
class ScheduleHandle:
    """Handle for a scheduled workflow."""

    schedule_id: str
    workflow_id: str


class WorkflowScheduler(ABC):
    """Scheduler interface. No cron or external scheduler implementations."""

    @abstractmethod
    def schedule(self, workflow: Workflow) -> ScheduleHandle:
        """Schedule a workflow for future execution."""

    @abstractmethod
    def cancel(self, schedule_id: str) -> None:
        """Cancel a scheduled workflow."""

    @abstractmethod
    def pause(self, schedule_id: str) -> None:
        """Pause a scheduled workflow."""

    @abstractmethod
    def resume(self, schedule_id: str) -> None:
        """Resume a paused scheduled workflow."""


class InMemoryWorkflowScheduler(WorkflowScheduler):
    """In-memory scheduler scaffold."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._schedules: dict[str, ScheduleHandle] = {}
        self._paused: set[str] = set()

    def schedule(self, workflow: Workflow) -> ScheduleHandle:
        schedule_id = str(uuid4())
        handle = ScheduleHandle(schedule_id=schedule_id, workflow_id=workflow.workflow_id)
        with self._lock:
            self._schedules[schedule_id] = handle
        return handle

    def cancel(self, schedule_id: str) -> None:
        with self._lock:
            self._schedules.pop(schedule_id, None)
            self._paused.discard(schedule_id)

    def pause(self, schedule_id: str) -> None:
        with self._lock:
            if schedule_id in self._schedules:
                self._paused.add(schedule_id)

    def resume(self, schedule_id: str) -> None:
        with self._lock:
            self._paused.discard(schedule_id)

    def is_paused(self, schedule_id: str) -> bool:
        with self._lock:
            return schedule_id in self._paused

    def list_schedules(self) -> tuple[ScheduleHandle, ...]:
        with self._lock:
            return tuple(self._schedules.values())
