"""Checkpoint registry."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from models.common import utc_now
from training_pipeline.checkpoints.training_checkpoint import TrainingCheckpoint
from training_pipeline.exceptions import CheckpointNotFoundError
from training_pipeline.jobs.training_job_status import TrainingJobStatus


class CheckpointRegistry:
    """Thread-safe registry for training checkpoints."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._checkpoints: dict[str, TrainingCheckpoint] = {}
        self._by_job: dict[str, tuple[str, ...]] = {}

    def create(
        self,
        *,
        job_id: str,
        experiment_id: str,
        run_id: str,
        status: TrainingJobStatus,
        step: int = 0,
        checksum: str = "",
    ) -> TrainingCheckpoint:
        checkpoint_id = f"checkpoint-{uuid4()}"
        checkpoint = TrainingCheckpoint(
            checkpoint_id=checkpoint_id,
            job_id=job_id,
            experiment_id=experiment_id,
            run_id=run_id,
            status=status,
            step=step,
            storage_uri=f"memory://checkpoints/{checkpoint_id}",
            checksum=checksum or checkpoint_id,
            created_at=utc_now(),
        )
        with self._lock:
            self._checkpoints[checkpoint_id] = checkpoint
            job_checkpoints = self._by_job.get(job_id, ())
            self._by_job[job_id] = (*job_checkpoints, checkpoint_id)
        return checkpoint

    def get(self, checkpoint_id: str) -> TrainingCheckpoint:
        with self._lock:
            checkpoint = self._checkpoints.get(checkpoint_id)
        if checkpoint is None:
            raise CheckpointNotFoundError(checkpoint_id)
        return checkpoint

    def list_for_job(self, job_id: str) -> tuple[TrainingCheckpoint, ...]:
        with self._lock:
            checkpoint_ids = self._by_job.get(job_id, ())
            return tuple(
                self._checkpoints[cid] for cid in checkpoint_ids if cid in self._checkpoints
            )

    def latest_for_job(self, job_id: str) -> TrainingCheckpoint:
        checkpoints = self.list_for_job(job_id)
        if not checkpoints:
            msg = f"No checkpoints found for job {job_id}"
            raise CheckpointNotFoundError(msg)
        return checkpoints[-1]

    def remove(self, checkpoint_id: str) -> None:
        with self._lock:
            checkpoint = self._checkpoints.pop(checkpoint_id, None)
            if checkpoint is None:
                raise CheckpointNotFoundError(checkpoint_id)
            job_checkpoints = self._by_job.get(checkpoint.job_id, ())
            self._by_job[checkpoint.job_id] = tuple(
                cid for cid in job_checkpoints if cid != checkpoint_id
            )
