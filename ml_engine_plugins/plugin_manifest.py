"""Plugin manifest contracts."""

from __future__ import annotations

from pydantic import Field

from ml_engine_plugins.plugin_capability import PluginCapability
from models.common import PlatformModel


class PluginManifest(PlatformModel):
    """Declarative manifest for an ML engine plugin."""

    plugin_id: str
    name: str
    version: str
    author: str = ""
    description: str = ""
    engine_type: str = "stub"
    capabilities: tuple[PluginCapability, ...] = ()
    entrypoint: str = ""
    attributes: dict[str, object] = Field(default_factory=dict)
