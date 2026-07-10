"""Storage provider type enumeration."""

from __future__ import annotations

from enum import StrEnum


class ProviderType(StrEnum):
    """Supported storage provider categories. Metadata only; no SDK bindings."""

    LOCAL = "local"
    FILE = "file"
    S3 = "s3"
    GCS = "gcs"
    AZURE = "azure"
    HTTP = "http"
    CUSTOM = "custom"
