"""Model artifact contract."""

from __future__ import annotations

from models.common import PlatformModel
from training_pipeline.artifacts.artifact_metadata import ArtifactManifest, ArtifactMetadata


class ModelArtifact(PlatformModel):
    """Infrastructure model artifact without framework serialization."""

    metadata: ArtifactMetadata
    manifest: ArtifactManifest
    storage_uri: str

    @property
    def artifact_id(self) -> str:
        return self.metadata.artifact_id
