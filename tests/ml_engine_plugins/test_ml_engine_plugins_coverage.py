"""Extended unit tests for ML engine plugin coverage."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from ml_engine_plugins import (
    PluginLifecycleEventType,
    PluginLifecycleManager,
    PluginNotFoundError,
    PluginRegistry,
    PluginValidationError,
    PluginValidator,
)
from tests.ml_engine_plugins_helpers import StubMLPlugin, make_plugin_bridge


@pytest.mark.unit
def test_plugin_loader_failure_emits_event() -> None:
    lifecycle = PluginLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    registry = PluginRegistry()
    from ml_engine_plugins import PluginLoader

    loader = PluginLoader(registry=registry, lifecycle=lifecycle)

    class BadPlugin(StubMLPlugin):
        def manifest(self):
            from ml_engine_plugins import PluginManifest

            return PluginManifest(
                plugin_id="",
                name="",
                version="",
            )

    with pytest.raises(PluginValidationError):
        loader.load(BadPlugin())
    types = {event.event_type for event in lifecycle.events}
    assert PluginLifecycleEventType.PLUGIN_FAILED in types


@pytest.mark.unit
def test_plugin_registry_get_plugin_missing() -> None:
    registry = PluginRegistry()
    with pytest.raises(PluginNotFoundError):
        registry.get_plugin("missing")


@pytest.mark.unit
def test_bridge_health_check_and_unload() -> None:
    _, bridge = make_plugin_bridge()
    bridge.register_provider(StubMLPlugin(plugin_id="health-engine"))
    bridge.discover_and_load()
    bridge.health_check("health-engine")
    bridge.unload("health-engine")


@pytest.mark.unit
def test_validator_manifest_errors() -> None:
    from ml_engine_plugins import PluginManifest

    validator = PluginValidator()
    result = validator.validate_manifest(
        PluginManifest(plugin_id="", name="", version=""),
    )
    with pytest.raises(PluginValidationError):
        validator.ensure_valid(result)
