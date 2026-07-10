"""Artifact summary contracts."""

from __future__ import annotations

from artifact_management.registry.artifact_record import ArtifactState
from models.common import PlatformModel


class ArtifactSummary(PlatformModel):
    """Summary record for a managed artifact."""

    artifact_id: str
    name: str
    version: str
    state: ArtifactState
    uri: str
