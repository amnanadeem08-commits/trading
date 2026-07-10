"""Plugin resource cleanup tests."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from pipeline import reset_pipeline_registry
from pipeline.context import PipelineContext
from plugins import PluginManager, PluginNotFoundError, reset_plugin_registry
from services import reset_application_context
from services.context import ApplicationContext, build_application_context
from tests.plugin_helpers import TestPlugin, make_plugin


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_pipeline_registry()
    reset_plugin_registry()
    yield
    reset_application_context()
    reset_pipeline_registry()
    reset_plugin_registry()


@pytest.mark.unit
def test_unload_cleans_health_metrics_and_subscriptions() -> None:
    bus = EventBus()
    application = build_application_context()
    updated_app = ApplicationContext(
        settings=application.settings,
        feature_flags=application.feature_flags,
        event_bus=bus,
        metrics=application.metrics,
        health=application.health,
        audit=application.audit,
        version_registry=application.version_registry,
        logger_factory=application.logger_factory,
        configuration_hash=application.configuration_hash,
    )
    context = PipelineContext(settings=updated_app.settings, application=updated_app)
    manager = PluginManager(context=context)
    manager.load(make_plugin(), TestPlugin())
    manager.enable("test-plugin")
    handles = manager.resource_handles("test-plugin")
    assert handles is not None
    assert handles.health_component == "plugin:test-plugin"
    assert bus.subscription_count() >= 1
    manager.unload("test-plugin")
    assert manager.resource_handles("test-plugin") is None
    assert bus.subscription_count() == 0
    assert updated_app.health.list_components() == ()


@pytest.mark.unit
def test_disable_resets_enabled_metric() -> None:
    manager = PluginManager()
    manager.load(make_plugin(), TestPlugin())
    manager.enable("test-plugin")
    gauge = manager._context.metrics.gauge("plugin.test-plugin.enabled")
    assert gauge.get() == 1
    manager.disable("test-plugin")
    assert gauge.get() == 0


@pytest.mark.unit
def test_unload_after_disable_removes_registry_entry() -> None:
    manager = PluginManager()
    plugin = make_plugin()
    manager.load(plugin, TestPlugin())
    manager.enable("test-plugin")
    manager.unload("test-plugin")
    assert manager.registry.exists("test-plugin") is False
    with pytest.raises(PluginNotFoundError):
        manager.get_state("test-plugin")
