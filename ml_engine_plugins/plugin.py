"""ML engine plugin contract."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ml_engine_plugins.plugin_capability import PluginCapability
from ml_engine_plugins.plugin_manifest import PluginManifest
from ml_engine_plugins.plugin_metadata import PluginMetadata
from ml_runtime.execution.model_executor import ModelExecutor


class MLPlugin(ABC):
    """Framework-agnostic ML engine plugin contract."""

    @abstractmethod
    def plugin_id(self) -> str:
        """Return the plugin identifier."""

    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""

    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return plugin manifest."""

    @abstractmethod
    def capabilities(self) -> tuple[PluginCapability, ...]:
        """Return supported capabilities."""

    @abstractmethod
    def create_executor(self) -> ModelExecutor:
        """Create a metadata-only executor adapter. No ML framework binding."""
