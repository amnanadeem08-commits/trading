"""Plugin capability contracts."""

from __future__ import annotations

from enum import StrEnum


class PluginCapability(StrEnum):
    """Capability flags for ML engine plugins."""

    LOAD = "load"
    EXECUTE = "execute"
    EXECUTE_BATCH = "execute_batch"
    UNLOAD = "unload"
    HEALTH = "health"
    METADATA = "metadata"
