"""Unit tests for core runtime."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from core import (
    CoreRuntime,
    DatasetLoadedEvent,
    get_core_runtime,
    reset_core_runtime,
)
from events.event_bus import EventBus
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_core_runtime()
    reset_settings()


@pytest.mark.unit
def test_runtime_initialize_builds_context() -> None:
    runtime = CoreRuntime()
    context = runtime.initialize()
    assert context.trace_id
    assert context.execution.configuration_hash
    assert runtime.active_context is not None


@pytest.mark.unit
def test_runtime_build_context_includes_dataset_and_plugin_ids() -> None:
    runtime = CoreRuntime()
    runtime.initialize()
    context = runtime.build_context(
        operation_type="load_dataset",
        dataset_ids=("records",),
        plugin_ids=("test-plugin",),
        principal_id="operator-1",
    )
    assert context.dataset_ids == ("records",)
    assert context.plugin_ids == ("test-plugin",)
    assert context.identity.principal_id == "operator-1"


@pytest.mark.unit
def test_runtime_publish_domain_event() -> None:
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
    context = build_pipeline_context(updated_app)
    runtime = CoreRuntime(context=context)
    runtime.initialize()
    event = DatasetLoadedEvent(
        event_id="evt-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        entity_id="records",
        dataset_id="records",
        dataset_version="1.0.0",
        record_count=2,
    )
    runtime.publish_domain_event(event)
    assert bus.persistence.count() == 2


@pytest.mark.unit
def test_runtime_shutdown_clears_active_context() -> None:
    runtime = CoreRuntime()
    runtime.initialize()
    runtime.shutdown()
    assert runtime.active_context is None


@pytest.mark.unit
def test_core_settings_loaded() -> None:
    settings = get_settings()
    assert settings.core.context_enabled is True
    assert settings.core.audit_enabled is True


@pytest.mark.unit
def test_get_core_runtime_singleton() -> None:
    first = get_core_runtime()
    second = get_core_runtime()
    assert first is second
