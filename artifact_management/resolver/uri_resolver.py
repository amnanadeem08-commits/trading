"""URI resolver for artifact locations."""

from __future__ import annotations

from artifact_management.exceptions import ArtifactResolutionError
from artifact_management.models.artifact_location import SUPPORTED_SCHEMES, ArtifactLocation


class URIResolver:
    """Resolves artifact URIs into location metadata without downloads."""

    def resolve(self, uri: str) -> ArtifactLocation:
        if not uri.strip():
            msg = "artifact URI must not be empty"
            raise ArtifactResolutionError(msg)
        try:
            location = ArtifactLocation.from_uri(uri)
        except ValueError as error:
            raise ArtifactResolutionError(str(error)) from error
        if location.scheme.value not in SUPPORTED_SCHEMES:
            msg = f"Unsupported artifact URI scheme: {location.scheme.value}"
            raise ArtifactResolutionError(msg)
        return location
