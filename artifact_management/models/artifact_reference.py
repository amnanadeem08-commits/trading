"""Artifact reference contracts."""

from __future__ import annotations

from pydantic import Field

from artifact_management.models.artifact_checksum import ArtifactChecksum
from artifact_management.models.artifact_location import ArtifactLocation
from models.common import PlatformModel, UTCDateTime


class ArtifactReference(PlatformModel):
    """Metadata reference to a platform artifact."""

    artifact_id: str
    uri: str
    checksum: ArtifactChecksum
    version: str
    format: str
    size: int = Field(ge=0, default=0)
    created_at: UTCDateTime | None = None
    location: ArtifactLocation | None = None
    attributes: dict[str, object] = Field(default_factory=dict)
