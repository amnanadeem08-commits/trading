"""Training checkpoint contract."""

from __future__ import annotations

from models.common import PlatformModel, UTCDateTime
from training_pipeline.jobs.training_job_status import TrainingJobStatus


class TrainingCheckpoint(PlatformModel):
    """Checkpoint metadata for a training job."""

    checkpoint_id: str
    job_id: str
    experiment_id: str
    run_id: str
    status: TrainingJobStatus
    step: int = 0
    storage_uri: str
    checksum: str
    created_at: UTCDateTime
