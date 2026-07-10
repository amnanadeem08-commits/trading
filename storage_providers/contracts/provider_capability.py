"""Storage provider capability enumeration."""

from __future__ import annotations

from enum import StrEnum


class ProviderCapability(StrEnum):
    """Declarative storage provider capabilities. Metadata only."""

    METADATA_RESOLUTION = "metadata_resolution"
    CHECKSUM_SUPPORT = "checksum_support"
    VERSIONING = "versioning"
    SIGNED_URLS = "signed_urls"
    CACHING = "caching"
