"""Adapter registry record."""

from __future__ import annotations

from enum import StrEnum

from framework_adapters.contracts.adapter_manifest import AdapterManifest
from framework_adapters.contracts.adapter_metadata import AdapterMetadata
from models.common import PlatformModel, UTCDateTime


class AdapterState(StrEnum):
    """Lifecycle state for framework adapters."""

    DISCOVERED = "discovered"
    REGISTERED = "registered"
    VALIDATED = "validated"
    LOADED = "loaded"
    HEALTHY = "healthy"
    SHUTDOWN = "shutdown"
    FAILED = "failed"


class AdapterRecord(PlatformModel):
    """Registered adapter record."""

    adapter_id: str
    metadata: AdapterMetadata
    manifest: AdapterManifest
    state: AdapterState
    priority: int = 0
    registered_at: UTCDateTime
    updated_at: UTCDateTime
