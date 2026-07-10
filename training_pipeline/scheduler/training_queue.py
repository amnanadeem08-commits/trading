"""Training job queue."""

from __future__ import annotations

from collections import deque
from threading import RLock

from training_pipeline.exceptions import TrainingJobNotFoundError
from training_pipeline.jobs.training_job import TrainingJob
from training_pipeline.jobs.training_job_status import TrainingJobStatus


class TrainingQueue:
    """Thread-safe FIFO queue for training jobs."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._queue: deque[TrainingJob] = deque()
        self._jobs: dict[str, TrainingJob] = {}

    def enqueue(self, job: TrainingJob) -> TrainingJob:
        queued = job.with_status(TrainingJobStatus.QUEUED)
        with self._lock:
            self._jobs[job.job_id] = queued
            self._queue.append(queued)
        return queued

    def dequeue(self) -> TrainingJob | None:
        with self._lock:
            if not self._queue:
                return None
            job = self._queue.popleft()
            self._jobs[job.job_id] = job.with_status(TrainingJobStatus.RUNNING)
            return self._jobs[job.job_id]

    def peek(self) -> TrainingJob | None:
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0]

    def get(self, job_id: str) -> TrainingJob:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise TrainingJobNotFoundError(job_id)
        return job

    def update(self, job: TrainingJob) -> None:
        with self._lock:
            self._jobs[job.job_id] = job

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def list_jobs(self) -> tuple[TrainingJob, ...]:
        with self._lock:
            return tuple(self._jobs[job_id] for job_id in sorted(self._jobs))
