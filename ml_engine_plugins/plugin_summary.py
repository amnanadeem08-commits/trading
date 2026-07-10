"""Plugin summary contracts."""

from __future__ import annotations

from ml_engine_plugins.plugin_state import PluginState
from models.common import PlatformModel


class PluginSummary(PlatformModel):
    """Summary for a single plugin."""

    plugin_id: str
    name: str
    version: str
    state: PluginState
    engine_type: str = "stub"
