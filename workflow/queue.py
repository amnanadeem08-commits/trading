"""In-memory workflow job queue."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from threading import RLock

from workflow.job import Job


class JobQueue(ABC):
    """Queue interface for workflow jobs."""

    @abstractmethod
    def enqueue(self, job: Job) -> None:
        """Add a job to the queue."""

    @abstractmethod
    def dequeue(self) -> Job | None:
        """Remove and return the next job, if any."""

    @abstractmethod
    def peek(self) -> Job | None:
        """Return the next job without removing it."""

    @abstractmethod
    def size(self) -> int:
        """Return the number of queued jobs."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all queued jobs."""


@dataclass(order=True)
class _PriorityJob:
    priority: int
    sequence: int
    job: Job = field(compare=False)


class InMemoryJobQueue(JobQueue):
    """Thread-safe in-memory FIFO queue with priority support."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._items: list[_PriorityJob] = []
        self._sequence = 0

    def enqueue(self, job: Job) -> None:
        with self._lock:
            self._sequence += 1
            self._items.append(_PriorityJob(-job.priority, self._sequence, job))
            self._items.sort()

    def dequeue(self) -> Job | None:
        with self._lock:
            if not self._items:
                return None
            return self._items.pop(0).job

    def peek(self) -> Job | None:
        with self._lock:
            if not self._items:
                return None
            return self._items[0].job

    def size(self) -> int:
        with self._lock:
            return len(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
