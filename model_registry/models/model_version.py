"""Model version contract."""

from __future__ import annotations

from model_registry.models.model_stage import ModelStage
from models.common import PlatformModel, UTCDateTime


class ModelVersion(PlatformModel):
    """Immutable version of a registered model."""

    version_id: str
    model_id: str
    semantic_version: str
    artifact_id: str
    dataset_id: str
    dataset_snapshot_id: str | None = None
    experiment_id: str
    run_id: str
    job_id: str
    config_hash: str
    checksum: str
    stage: ModelStage = ModelStage.DRAFT
    created_at: UTCDateTime
    immutable: bool = True
