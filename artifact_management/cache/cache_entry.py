"""Artifact cache entry."""

from __future__ import annotations

from artifact_management.models.artifact_reference import ArtifactReference
from models.common import PlatformModel, UTCDateTime


class CacheEntry(PlatformModel):
    """Metadata cache entry for a resolved artifact."""

    artifact_id: str
    reference: ArtifactReference
    cached_at: UTCDateTime
    hit_count: int = 0
