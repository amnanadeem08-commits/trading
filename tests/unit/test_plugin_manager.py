"""Unit tests for plugin manager."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from pipeline import build_pipeline_context, reset_pipeline_registry
from pipeline.context import PipelineContext
from plugins import (
    PluginLifecycleEventType,
    PluginManager,
    PluginNotFoundError,
    PluginState,
    PluginValidationError,
    reset_plugin_registry,
)
from services import reset_application_context
from services.context import ApplicationContext
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
def test_manager_load_enable_disable() -> None:
    manager = PluginManager()
    plugin = make_plugin()
    loaded = manager.load(plugin, TestPlugin())
    assert loaded.state == PluginState.LOADED
    assert manager.enable("test-plugin") == PluginState.ENABLED
    assert manager.disable("test-plugin") == PluginState.DISABLED


@pytest.mark.unit
def test_manager_unload_and_reload() -> None:
    manager = PluginManager()
    plugin = make_plugin()
    manager.load(plugin, TestPlugin())
    manager.unload("test-plugin")
    with pytest.raises(PluginNotFoundError):
        manager.get_state("test-plugin")
    reloaded = manager.reload("test-plugin", plugin, TestPlugin())
    assert reloaded.definition.plugin_id == "test-plugin"


@pytest.mark.unit
def test_manager_discover_emits_events() -> None:
    manager = PluginManager()
    plugins = manager.discover(modules=("tests.plugin_helpers",))
    assert len(plugins) >= 1
    event_types = {event.event_type for event in manager.lifecycle.events}
    assert PluginLifecycleEventType.PLUGIN_DISCOVERED in event_types


@pytest.mark.unit
def test_manager_validation_failure_emits_failed_event() -> None:
    manager = PluginManager()
    invalid = make_plugin(version="9.9.9")
    invalid = invalid.model_copy(
        update={
            "manifest": invalid.manifest.model_copy(
                update={
                    "platform_version": invalid.manifest.platform_version.model_copy(
                        update={"minimum": "99.0.0"},
                    ),
                },
            ),
        },
    )
    with pytest.raises(PluginValidationError):
        manager.load(invalid, TestPlugin())
    event_types = {event.event_type for event in manager.lifecycle.events}
    assert PluginLifecycleEventType.PLUGIN_FAILED in event_types


@pytest.mark.unit
def test_manager_publishes_events_to_event_bus() -> None:
    bus = EventBus()
    application = build_pipeline_context().application
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
    assert bus.persistence.count() >= 1
