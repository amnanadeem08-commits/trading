"""Training result contract."""

from __future__ import annotations

from models.common import PlatformModel, UTCDateTime
from training_pipeline.jobs.training_job_status import TrainingJobStatus


class TrainingResult(PlatformModel):
    """Outcome of a training job execution."""

    job_id: str
    experiment_id: str
    run_id: str
    status: TrainingJobStatus
    artifact_id: str | None = None
    checkpoint_id: str | None = None
    dataset_snapshot_id: str | None = None
    training_version: str = ""
    message: str = ""
    completed_at: UTCDateTime | None = None
