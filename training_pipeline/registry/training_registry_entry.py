"""Training registry entry contract."""

from __future__ import annotations

from models.common import PlatformModel, UTCDateTime
from training_pipeline.jobs.training_job_status import TrainingJobStatus


class TrainingRegistryEntry(PlatformModel):
    """Indexed training job record."""

    job_id: str
    experiment_id: str
    run_id: str | None
    status: TrainingJobStatus
    artifact_id: str | None
    checkpoint_id: str | None
    training_version: str
    registered_at: UTCDateTime
    updated_at: UTCDateTime
