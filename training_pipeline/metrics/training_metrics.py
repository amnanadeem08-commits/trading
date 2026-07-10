"""Training metrics collection."""

from __future__ import annotations

from threading import RLock

from models.common import PlatformModel
from training_pipeline.jobs.training_job_status import TrainingJobStatus


class TrainingStatistics(PlatformModel):
    """Aggregate training statistics."""

    total_jobs: int = 0
    queued_jobs: int = 0
    running_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    cancelled_jobs: int = 0
    total_artifacts: int = 0
    total_checkpoints: int = 0


class TrainingSummary(PlatformModel):
    """Summary for a single training job."""

    job_id: str
    experiment_id: str
    status: TrainingJobStatus
    duration_seconds: float = 0.0
    artifact_stored: bool = False
    checkpoint_count: int = 0


class TrainingMetricsCollector:
    """Collects training pipeline metrics."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._status_counts: dict[TrainingJobStatus, int] = {
            status: 0 for status in TrainingJobStatus
        }
        self._artifact_count = 0
        self._checkpoint_count = 0
        self._summaries: dict[str, TrainingSummary] = {}

    def record_status(self, status: TrainingJobStatus) -> None:
        with self._lock:
            self._status_counts[status] = self._status_counts.get(status, 0) + 1

    def record_artifact(self) -> None:
        with self._lock:
            self._artifact_count += 1

    def record_checkpoint(self) -> None:
        with self._lock:
            self._checkpoint_count += 1

    def record_summary(self, summary: TrainingSummary) -> None:
        with self._lock:
            self._summaries[summary.job_id] = summary

    def statistics(self) -> TrainingStatistics:
        with self._lock:
            total = sum(self._status_counts.values())
            return TrainingStatistics(
                total_jobs=total,
                queued_jobs=self._status_counts.get(TrainingJobStatus.QUEUED, 0),
                running_jobs=self._status_counts.get(TrainingJobStatus.RUNNING, 0),
                completed_jobs=self._status_counts.get(TrainingJobStatus.COMPLETED, 0),
                failed_jobs=self._status_counts.get(TrainingJobStatus.FAILED, 0),
                cancelled_jobs=self._status_counts.get(TrainingJobStatus.CANCELLED, 0),
                total_artifacts=self._artifact_count,
                total_checkpoints=self._checkpoint_count,
            )

    def get_summary(self, job_id: str) -> TrainingSummary | None:
        with self._lock:
            return self._summaries.get(job_id)
