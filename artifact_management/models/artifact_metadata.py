"""Artifact metadata contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime


class ArtifactMetadata(PlatformModel):
    """Metadata for a registered artifact."""

    artifact_id: str
    name: str
    version: str
    format: str = ""
    engine_type: str = ""
    description: str = ""
    registered_at: UTCDateTime | None = None
    attributes: dict[str, object] = Field(default_factory=dict)
