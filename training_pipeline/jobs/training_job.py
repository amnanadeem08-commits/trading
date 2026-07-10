"""Training job entity."""

from __future__ import annotations

from models.common import PlatformModel, UTCDateTime, utc_now
from training_pipeline.jobs.training_job_spec import TrainingJobSpec
from training_pipeline.jobs.training_job_status import TrainingJobStatus


class TrainingJob(PlatformModel):
    """Orchestration record for a single training job."""

    spec: TrainingJobSpec
    status: TrainingJobStatus = TrainingJobStatus.PENDING
    run_id: str | None = None
    artifact_id: str | None = None
    checkpoint_id: str | None = None
    error_message: str | None = None
    created_at: UTCDateTime
    updated_at: UTCDateTime
    started_at: UTCDateTime | None = None
    completed_at: UTCDateTime | None = None

    @classmethod
    def from_spec(cls, spec: TrainingJobSpec) -> TrainingJob:
        now = utc_now()
        return cls(spec=spec, created_at=now, updated_at=now)

    def with_status(self, status: TrainingJobStatus, *, message: str | None = None) -> TrainingJob:
        now = utc_now()
        updates: dict[str, object] = {"status": status, "updated_at": now}
        if status == TrainingJobStatus.RUNNING:
            updates["started_at"] = now
        if status.is_terminal():
            updates["completed_at"] = now
        if message is not None:
            updates["error_message"] = message
        return self.model_copy(update=updates)

    @property
    def job_id(self) -> str:
        return self.spec.job_id
