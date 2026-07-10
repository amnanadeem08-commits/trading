"""Integration tests for core layer runtime."""

from __future__ import annotations

import pytest

from config.settings import get_settings, reset_settings
from core import (
    CoreLifecycleEventType,
    CoreRuntime,
    DatasetLoadedEvent,
    EntityRegistry,
    get_core_runtime,
    get_entity_registry,
    reset_core_runtime,
    reset_entity_registry,
)
from events.event_bus import EventBus
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context
from tests.core_helpers import make_entity


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_entity_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_entity_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_core_runtime_initialize_and_context_flow() -> None:
    settings = get_settings()
    assert settings.core.context_enabled is True
    assert settings.core.lifecycle_enabled is True

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

    root_context = runtime.initialize()
    operation_context = runtime.build_context(
        operation_type="process_records",
        dataset_ids=("records",),
        plugin_ids=("test-plugin",),
    )

    assert root_context.trace_id == operation_context.trace_id
    assert operation_context.audit.dataset_ids == ("records",)
    assert operation_context.audit.plugin_ids == ("test-plugin",)
    assert runtime.lifecycle.events
    assert bus.persistence.count() >= 2


@pytest.mark.integration
def test_core_runtime_entity_registry_and_domain_event() -> None:
    registry = EntityRegistry()
    entity = make_entity(entity_id="records")
    registry.register(entity)
    validation = registry.validate(entity)
    assert validation.valid is True

    runtime = CoreRuntime()
    runtime.initialize()
    event = DatasetLoadedEvent(
        event_id="evt-runtime",
        correlation_id=runtime.active_context.correlation_id if runtime.active_context else "corr",
        trace_id=runtime.active_context.trace_id if runtime.active_context else "trace",
        entity_id="records",
        dataset_id="records",
        dataset_version="1.0.0",
        record_count=2,
    )
    runtime.publish_domain_event(event)

    event_types = {item.event_type for item in runtime.lifecycle.events}
    assert CoreLifecycleEventType.RUNTIME_INITIALIZED in event_types
    assert registry.list() == ("records",)


@pytest.mark.integration
def test_core_runtime_singleton_registry() -> None:
    registry = get_entity_registry()
    entity = make_entity(entity_id="singleton")
    registry.register(entity)
    assert get_entity_registry().exists("singleton") is True
    assert get_core_runtime() is get_core_runtime()
