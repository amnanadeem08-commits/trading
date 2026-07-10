"""Unit tests for plugin versioning."""

from __future__ import annotations

import pytest

from ml_engine_plugins import MLEnginePluginError, PluginVersionRegistry


@pytest.mark.unit
def test_plugin_version_registry() -> None:
    registry = PluginVersionRegistry()
    version = registry.register(
        version_id="plugins-v1",
        framework_schema="1.0.0",
        configuration_hash="hash",
    )
    assert version.version_id == "plugins-v1"
    assert registry.latest() == version


@pytest.mark.unit
def test_plugin_version_registry_errors() -> None:
    registry = PluginVersionRegistry()
    with pytest.raises(MLEnginePluginError):
        registry.register(version_id="", framework_schema="1.0.0")
