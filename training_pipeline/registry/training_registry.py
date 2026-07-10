"""Training registry."""

from __future__ import annotations

from threading import RLock

from models.common import utc_now
from training_pipeline.exceptions import TrainingJobNotFoundError
from training_pipeline.jobs.training_job import TrainingJob
from training_pipeline.jobs.training_job_status import TrainingJobStatus
from training_pipeline.registry.training_registry_entry import TrainingRegistryEntry


class TrainingRegistry:
    """Thread-safe registry for training job records."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, TrainingRegistryEntry] = {}

    def register_job(self, job: TrainingJob) -> TrainingRegistryEntry:
        now = utc_now()
        entry = TrainingRegistryEntry(
            job_id=job.job_id,
            experiment_id=job.spec.experiment_id,
            run_id=job.run_id,
            status=job.status,
            artifact_id=job.artifact_id,
            checkpoint_id=job.checkpoint_id,
            training_version=job.spec.training_version,
            registered_at=now,
            updated_at=now,
        )
        with self._lock:
            self._entries[job.job_id] = entry
        return entry

    def update_job(self, job: TrainingJob) -> TrainingRegistryEntry:
        with self._lock:
            existing = self._entries.get(job.job_id)
            if existing is None:
                return self.register_job(job)
            entry = existing.model_copy(
                update={
                    "run_id": job.run_id,
                    "status": job.status,
                    "artifact_id": job.artifact_id,
                    "checkpoint_id": job.checkpoint_id,
                    "updated_at": utc_now(),
                }
            )
            self._entries[job.job_id] = entry
            return entry

    def get(self, job_id: str) -> TrainingRegistryEntry:
        with self._lock:
            entry = self._entries.get(job_id)
        if entry is None:
            raise TrainingJobNotFoundError(job_id)
        return entry

    def list_entries(self) -> tuple[TrainingRegistryEntry, ...]:
        with self._lock:
            return tuple(self._entries[job_id] for job_id in sorted(self._entries))

    def list_by_status(self, status: TrainingJobStatus) -> tuple[TrainingRegistryEntry, ...]:
        return tuple(entry for entry in self.list_entries() if entry.status == status)
