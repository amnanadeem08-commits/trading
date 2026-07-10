"""Plugin metadata contracts."""

from __future__ import annotations

from models.common import PlatformModel, UTCDateTime


class PluginMetadata(PlatformModel):
    """Metadata for an ML engine plugin."""

    plugin_id: str
    name: str
    version: str
    author: str = ""
    description: str = ""
    engine_type: str = "stub"
    registered_at: UTCDateTime | None = None
