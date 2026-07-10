"""Plugin state contracts."""

from __future__ import annotations

from enum import StrEnum


class PluginState(StrEnum):
    """Lifecycle state for ML engine plugins."""

    DISCOVERED = "discovered"
    REGISTERED = "registered"
    LOADED = "loaded"
    VALIDATED = "validated"
    HEALTHY = "healthy"
    UNLOADED = "unloaded"
    FAILED = "failed"
