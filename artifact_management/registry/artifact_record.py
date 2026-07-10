"""Artifact registry record."""

from __future__ import annotations

from enum import StrEnum

from artifact_management.models.artifact_manifest import ArtifactManifest
from artifact_management.models.artifact_metadata import ArtifactMetadata
from artifact_management.models.artifact_reference import ArtifactReference
from models.common import PlatformModel, UTCDateTime


class ArtifactState(StrEnum):
    """Lifecycle state for managed artifacts."""

    REGISTERED = "registered"
    RESOLVED = "resolved"
    VALIDATED = "validated"
    CACHED = "cached"
    EXPIRED = "expired"
    FAILED = "failed"


class ArtifactRecord(PlatformModel):
    """Registered artifact record."""

    artifact_id: str
    metadata: ArtifactMetadata
    manifest: ArtifactManifest
    reference: ArtifactReference
    state: ArtifactState
    registered_at: UTCDateTime
    updated_at: UTCDateTime
