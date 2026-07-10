"""Unit tests for plugin lifecycle."""

from __future__ import annotations

import pytest

from pipeline import build_pipeline_context, reset_pipeline_registry
from plugins import (
    PluginLifecycle,
    PluginLifecycleEventType,
    PluginLifecycleManager,
    PluginState,
    PluginStateError,
    reset_plugin_registry,
)
from services import reset_application_context
from tests.plugin_helpers import TestPlugin


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
def test_plugin_lifecycle_transitions() -> None:
    lifecycle = PluginLifecycle(TestPlugin())
    assert lifecycle.initialize() == PluginState.INITIALIZED
    assert lifecycle.start() == PluginState.ENABLED
    assert lifecycle.stop() == PluginState.STOPPED
    assert lifecycle.dispose() == PluginState.DISABLED


@pytest.mark.unit
def test_plugin_lifecycle_invalid_transition_raises() -> None:
    lifecycle = PluginLifecycle(TestPlugin())
    with pytest.raises(PluginStateError):
        lifecycle.start()


@pytest.mark.unit
def test_lifecycle_manager_emits_and_publishes() -> None:
    context = build_pipeline_context()
    lifecycle = PluginLifecycleManager(context)
    seen: list[str] = []
    lifecycle.on_event(lambda event: seen.append(event.event_type.value))
    lifecycle.emit(
        PluginLifecycleEventType.PLUGIN_LOADED,
        plugin_id="test-plugin",
        plugin_version="1.0.0",
        correlation_id="corr-1",
        message="loaded",
    )
    assert seen == ["plugin_loaded"]
    assert len(lifecycle.events) == 1


@pytest.mark.unit
def test_lifecycle_off_event() -> None:
    context = build_pipeline_context()
    lifecycle = PluginLifecycleManager(context)
    seen: list[str] = []
    subscription = lifecycle.on_event(lambda event: seen.append(event.event_type.value))
    lifecycle.off_event(subscription)
    lifecycle.emit(
        PluginLifecycleEventType.PLUGIN_DISCOVERED,
        plugin_id="test-plugin",
        plugin_version="1.0.0",
        correlation_id="corr-1",
        message="discovered",
    )
    assert seen == []
