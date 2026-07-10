"""Model artifact metadata contracts."""

from __future__ import annotations

from typing import Any

from models.common import PlatformModel, UTCDateTime
from training_pipeline.datasets.dataset_reference import DatasetReference


class ArtifactMetadata(PlatformModel):
    """Metadata for a stored model artifact."""

    artifact_id: str
    experiment_id: str
    run_id: str
    job_id: str
    model_family: str
    training_version: str
    dataset: DatasetReference
    checksum: str
    size_bytes: int = 0
    tags: tuple[str, ...] = ()
    created_at: UTCDateTime


class ArtifactManifest(PlatformModel):
    """Manifest describing artifact contents without framework bindings."""

    artifact_id: str
    format_version: str = "1.0.0"
    files: tuple[str, ...] = ()
    hyperparameters: dict[str, Any]
    lineage: tuple[str, ...] = ()
    reproducibility_key: str = ""
