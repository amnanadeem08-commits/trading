"""Integration tests for plugin runtime flow."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from pipeline import reset_pipeline_registry
from pipeline.context import PipelineContext
from plugins import (
    PluginLifecycleEventType,
    PluginManager,
    PluginRegistry,
    PluginState,
    reset_plugin_manager,
    reset_plugin_registry,
)
from services import reset_application_context
from services.context import ApplicationContext, build_application_context
from tests.plugin_helpers import TestPlugin


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_pipeline_registry()
    reset_plugin_registry()
    reset_plugin_manager()
    yield
    reset_application_context()
    reset_pipeline_registry()
    reset_plugin_registry()
    reset_plugin_manager()


@pytest.mark.integration
def test_full_plugin_runtime_flow() -> None:
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
    registry = PluginRegistry()
    manager = PluginManager(context=context, registry=registry)

    discovered = manager.discover(modules=("tests.plugin_helpers",))
    assert len(discovered) >= 1
    plugin_def = discovered[0]

    loaded = manager.load(plugin_def, TestPlugin())
    assert loaded.state == PluginState.LOADED
    assert registry.exists(plugin_def.plugin_id)

    enabled = manager.enable(plugin_def.plugin_id)
    assert enabled == PluginState.ENABLED
    assert manager.get_state(plugin_def.plugin_id) == PluginState.ENABLED

    event_types = {event.event_type for event in manager.lifecycle.events}
    assert PluginLifecycleEventType.PLUGIN_DISCOVERED in event_types
    assert PluginLifecycleEventType.PLUGIN_LOADED in event_types
    assert PluginLifecycleEventType.PLUGIN_ENABLED in event_types
    assert bus.persistence.count() >= 3

    manager.disable(plugin_def.plugin_id)
    assert manager.get_state(plugin_def.plugin_id) == PluginState.DISABLED

    manager.unload(plugin_def.plugin_id)
    assert registry.exists(plugin_def.plugin_id) is False
    assert bus.subscription_count() == 0
