"""Plugin registry record."""

from __future__ import annotations

from ml_engine_plugins.plugin_manifest import PluginManifest
from ml_engine_plugins.plugin_metadata import PluginMetadata
from ml_engine_plugins.plugin_state import PluginState
from models.common import PlatformModel, UTCDateTime


class PluginRecord(PlatformModel):
    """Registered plugin record."""

    plugin_id: str
    metadata: PluginMetadata
    manifest: PluginManifest
    state: PluginState
    registered_at: UTCDateTime
    updated_at: UTCDateTime
