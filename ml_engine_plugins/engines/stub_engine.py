"""Concrete stub ML engine plugin."""

from __future__ import annotations

from ml_engine_plugins.engines.stub_executor import STUB_ENGINE_ID, StubModelExecutor
from ml_engine_plugins.plugin import MLPlugin
from ml_engine_plugins.plugin_capability import PluginCapability
from ml_engine_plugins.plugin_manifest import PluginManifest
from ml_engine_plugins.plugin_metadata import PluginMetadata
from ml_runtime.execution.model_executor import ModelExecutor
from models.common import utc_now

STUB_ENGINE_VERSION = "1.0.0"
STUB_ENGINE_NAME = "Stub ML Engine"

__all__ = [
    "STUB_ENGINE_ID",
    "STUB_ENGINE_NAME",
    "STUB_ENGINE_VERSION",
    "StubMLEnginePlugin",
    "create_stub_engine",
]


class StubMLEnginePlugin(MLPlugin):
    """Concrete stub engine proving the plugin registration path."""

    def __init__(
        self,
        *,
        plugin_id: str = STUB_ENGINE_ID,
        name: str = STUB_ENGINE_NAME,
        version: str = STUB_ENGINE_VERSION,
    ) -> None:
        self._plugin_id = plugin_id
        self._name = name
        self._version = version

    def plugin_id(self) -> str:
        return self._plugin_id

    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            plugin_id=self._plugin_id,
            name=self._name,
            version=self._version,
            author="platform",
            description="Concrete stub ML engine for plugin architecture validation",
            engine_type="stub",
            registered_at=utc_now(),
        )

    def manifest(self) -> PluginManifest:
        return PluginManifest(
            plugin_id=self._plugin_id,
            name=self._name,
            version=self._version,
            author="platform",
            description="Concrete stub ML engine for plugin architecture validation",
            engine_type="stub",
            capabilities=(
                PluginCapability.LOAD,
                PluginCapability.EXECUTE,
                PluginCapability.EXECUTE_BATCH,
                PluginCapability.UNLOAD,
                PluginCapability.HEALTH,
                PluginCapability.METADATA,
            ),
            entrypoint="ml_engine_plugins.engines.stub_engine",
            attributes={"sandbox": True},
        )

    def capabilities(self) -> tuple[PluginCapability, ...]:
        return self.manifest().capabilities

    def create_executor(self) -> ModelExecutor:
        return StubModelExecutor(executor_id=self._plugin_id)


def create_stub_engine() -> StubMLEnginePlugin:
    """Create the default stub ML engine plugin."""
    return StubMLEnginePlugin()
