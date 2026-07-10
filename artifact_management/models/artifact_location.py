"""Artifact location URI abstraction."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel


class ArtifactScheme(StrEnum):
    """Supported URI schemes. Metadata only; no SDK bindings."""

    LOCAL = "local"
    FILE = "file"
    S3 = "s3"
    GS = "gs"
    AZURE = "azure"
    HTTP = "http"


SUPPORTED_SCHEMES: frozenset[str] = frozenset(scheme.value for scheme in ArtifactScheme)


class ArtifactLocation(PlatformModel):
    """URI abstraction for artifact storage locations."""

    uri: str
    scheme: ArtifactScheme
    path: str = ""
    bucket: str = ""
    attributes: dict[str, object] = Field(default_factory=dict)

    @classmethod
    def from_uri(cls, uri: str) -> ArtifactLocation:
        """Parse a URI into location metadata without accessing storage."""
        if "://" not in uri:
            msg = f"Invalid artifact URI: {uri}"
            raise ValueError(msg)
        scheme_value, remainder = uri.split("://", 1)
        try:
            scheme = ArtifactScheme(scheme_value.lower())
        except ValueError as error:
            msg = f"Unsupported artifact URI scheme: {scheme_value}"
            raise ValueError(msg) from error
        bucket = ""
        path = remainder
        if scheme in {ArtifactScheme.S3, ArtifactScheme.GS, ArtifactScheme.AZURE}:
            parts = remainder.split("/", 1)
            bucket = parts[0]
            path = parts[1] if len(parts) > 1 else ""
        return cls(uri=uri, scheme=scheme, path=path, bucket=bucket)
