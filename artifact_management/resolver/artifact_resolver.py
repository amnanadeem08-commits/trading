"""Artifact resolver."""

from __future__ import annotations

from artifact_management.exceptions import ArtifactResolutionError
from artifact_management.models.artifact_manifest import ArtifactManifest
from artifact_management.models.artifact_metadata import ArtifactMetadata
from artifact_management.models.artifact_reference import ArtifactReference


class ArtifactResolver:
    """Validates artifact references resolved by the storage provider layer."""

    def resolve(
        self,
        *,
        reference: ArtifactReference,
        metadata: ArtifactMetadata | None = None,
        manifest: ArtifactManifest | None = None,
    ) -> ArtifactReference:
        if metadata is not None and metadata.artifact_id != reference.artifact_id:
            msg = "metadata.artifact_id does not match reference.artifact_id"
            raise ArtifactResolutionError(msg)
        if manifest is not None and manifest.artifact_id != reference.artifact_id:
            msg = "manifest.artifact_id does not match reference.artifact_id"
            raise ArtifactResolutionError(msg)
        if reference.location is None:
            msg = (
                "artifact location must be resolved through storage provider bridge "
                "before artifact resolution"
            )
            raise ArtifactResolutionError(msg)
        return reference
