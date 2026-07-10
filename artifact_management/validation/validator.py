"""Artifact validator."""

from __future__ import annotations

from artifact_management.exceptions import ArtifactNotFoundError, ArtifactValidationError
from artifact_management.models.artifact_manifest import ArtifactManifest
from artifact_management.models.artifact_metadata import ArtifactMetadata
from artifact_management.models.artifact_reference import ArtifactReference
from artifact_management.registry.artifact_registry import ArtifactRegistry
from artifact_management.validation.validation_result import ArtifactValidationResult


class ArtifactValidator:
    """Validates artifact contracts without file access."""

    def __init__(self, *, registry: ArtifactRegistry | None = None) -> None:
        self._registry = registry

    def validate_uri(self, uri: str) -> ArtifactValidationResult:
        errors: list[str] = []
        if not uri.strip():
            errors.append("uri must not be empty")
        elif "://" not in uri:
            errors.append("uri must include a scheme")
        if errors:
            return ArtifactValidationResult.failure(*errors)
        return ArtifactValidationResult.success()

    def validate_checksum(self, reference: ArtifactReference) -> ArtifactValidationResult:
        if not reference.checksum.validate_format():
            return ArtifactValidationResult.failure(
                "checksum value format is invalid",
                artifact_id=reference.artifact_id,
            )
        return ArtifactValidationResult.success(artifact_id=reference.artifact_id)

    def validate_metadata(self, metadata: ArtifactMetadata) -> ArtifactValidationResult:
        errors: list[str] = []
        if not metadata.artifact_id.strip():
            errors.append("artifact_id must not be empty")
        if not metadata.name.strip():
            errors.append("name must not be empty")
        if not metadata.version.strip():
            errors.append("version must not be empty")
        if errors:
            return ArtifactValidationResult.failure(
                *errors,
                artifact_id=metadata.artifact_id or None,
            )
        return ArtifactValidationResult.success(artifact_id=metadata.artifact_id)

    def validate_manifest(self, manifest: ArtifactManifest) -> ArtifactValidationResult:
        errors: list[str] = []
        if not manifest.artifact_id.strip():
            errors.append("artifact_id must not be empty")
        if not manifest.name.strip():
            errors.append("name must not be empty")
        if not manifest.version.strip():
            errors.append("version must not be empty")
        if errors:
            return ArtifactValidationResult.failure(
                *errors,
                artifact_id=manifest.artifact_id or None,
            )
        return ArtifactValidationResult.success(artifact_id=manifest.artifact_id)

    def validate_duplicate_registration(
        self,
        artifact_id: str,
    ) -> ArtifactValidationResult:
        if self._registry is None:
            return ArtifactValidationResult.success(artifact_id=artifact_id)
        try:
            self._registry.lookup(artifact_id)
        except ArtifactNotFoundError:
            return ArtifactValidationResult.success(artifact_id=artifact_id)
        return ArtifactValidationResult.failure(
            "artifact already registered",
            artifact_id=artifact_id,
        )

    def validate_reference(
        self,
        *,
        reference: ArtifactReference,
        metadata: ArtifactMetadata,
        manifest: ArtifactManifest,
    ) -> ArtifactValidationResult:
        uri_result = self.validate_uri(reference.uri)
        if not uri_result.valid:
            return uri_result
        checksum_result = self.validate_checksum(reference)
        if not checksum_result.valid:
            return checksum_result
        metadata_result = self.validate_metadata(metadata)
        if not metadata_result.valid:
            return metadata_result
        manifest_result = self.validate_manifest(manifest)
        if not manifest_result.valid:
            return manifest_result
        if metadata.artifact_id != reference.artifact_id:
            return ArtifactValidationResult.failure(
                "metadata.artifact_id must match reference.artifact_id",
                artifact_id=reference.artifact_id,
            )
        if manifest.artifact_id != reference.artifact_id:
            return ArtifactValidationResult.failure(
                "manifest.artifact_id must match reference.artifact_id",
                artifact_id=reference.artifact_id,
            )
        duplicate_result = self.validate_duplicate_registration(reference.artifact_id)
        if not duplicate_result.valid:
            return duplicate_result
        return ArtifactValidationResult.success(artifact_id=reference.artifact_id)

    def ensure_valid(self, result: ArtifactValidationResult) -> None:
        if not result.valid:
            message = result.errors[0] if result.errors else "validation failed"
            raise ArtifactValidationError(message)
