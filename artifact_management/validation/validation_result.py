"""Artifact validation result."""

from __future__ import annotations

from models.common import PlatformModel


class ArtifactValidationResult(PlatformModel):
    """Validation result for artifact operations."""

    valid: bool
    errors: tuple[str, ...] = ()
    artifact_id: str | None = None

    @classmethod
    def success(cls, *, artifact_id: str | None = None) -> ArtifactValidationResult:
        return cls(valid=True, artifact_id=artifact_id)

    @classmethod
    def failure(cls, *errors: str, artifact_id: str | None = None) -> ArtifactValidationResult:
        return cls(valid=False, errors=errors, artifact_id=artifact_id)
