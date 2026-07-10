"""Plugin lifecycle state definitions."""

from __future__ import annotations

from enum import StrEnum


class PluginState(StrEnum):
    """Plugin lifecycle states."""

    DISCOVERED = "discovered"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ENABLED = "enabled"
    DISABLED = "disabled"
    STOPPED = "stopped"
    FAILED = "failed"


TERMINAL_PLUGIN_STATES: frozenset[PluginState] = frozenset(
    {
        PluginState.DISABLED,
        PluginState.STOPPED,
        PluginState.FAILED,
    }
)
