"""Plugin domain contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic import Field

from models.common import PlatformModel
from plugins.manifest import PluginManifest
from plugins.state import PluginState


class Plugin(PlatformModel):
    """Registered plugin definition."""

    plugin_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    author: str = Field(min_length=1)
    description: str = ""
    manifest: PluginManifest


class BasePlugin(ABC):
    """Executable plugin implementation contract."""

    @abstractmethod
    def plugin_id(self) -> str:
        """Return the plugin identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the plugin display name."""

    @abstractmethod
    def version(self) -> str:
        """Return the plugin version."""

    @abstractmethod
    def author(self) -> str:
        """Return the plugin author."""

    @abstractmethod
    def description(self) -> str:
        """Return the plugin description."""

    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""

    def to_definition(self) -> Plugin:
        """Convert the plugin implementation to a registered definition."""
        return Plugin(
            plugin_id=self.plugin_id(),
            name=self.name(),
            version=self.version(),
            author=self.author(),
            description=self.description(),
            manifest=self.manifest(),
        )


@dataclass
class LoadedPlugin:
    """Plugin instance tracked by the manager."""

    definition: Plugin
    implementation: BasePlugin | None = None
    state: PluginState = PluginState.DISCOVERED
