"""Provider record contracts."""

from __future__ import annotations

from enum import StrEnum

from models.common import PlatformModel, UTCDateTime
from storage_providers.contracts.provider_manifest import ProviderManifest
from storage_providers.contracts.provider_metadata import ProviderMetadata


class ProviderState(StrEnum):
    """Lifecycle state for a registered storage provider."""

    REGISTERED = "registered"
    VALIDATED = "validated"
    RESOLVED = "resolved"
    HEALTHY = "healthy"
    FAILED = "failed"
    SHUTDOWN = "shutdown"


class ProviderRecord(PlatformModel):
    """Registry record for a storage provider."""

    provider_id: str
    metadata: ProviderMetadata
    manifest: ProviderManifest
    state: ProviderState
    registered_at: UTCDateTime
    updated_at: UTCDateTime
