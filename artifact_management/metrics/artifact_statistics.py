"""Artifact statistics contracts."""

from __future__ import annotations

from models.common import PlatformModel


class ArtifactStatistics(PlatformModel):
    """Aggregate statistics for artifact management."""

    total_artifacts: int
    registered_artifacts: int
    resolved_artifacts: int
    validated_artifacts: int
    cached_artifacts: int
    expired_artifacts: int
    failed_artifacts: int
    artifact_registrations: int
    artifact_resolutions: int
    artifact_validations: int
    cache_hits: int
    cache_misses: int
    artifact_failures: int
