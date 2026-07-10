"""Unit tests for dataset lifecycle."""

from __future__ import annotations

import pytest

from data import DatasetLifecycleEventType, DatasetLifecycleManager
from events.event_bus import EventBus
from pipeline import build_pipeline_context
from pipeline.context import PipelineContext
from services import reset_application_context
from services.context import ApplicationContext, build_application_context
from tests.data_helpers import make_dataset


@pytest.fixture(autouse=True)
def _reset_context() -> None:
    reset_application_context()
    yield
    reset_application_context()


def _context_with_bus(bus: EventBus) -> PipelineContext:
    application = build_application_context()
    updated = ApplicationContext(
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
    return PipelineContext(settings=updated.settings, application=updated)


@pytest.mark.unit
def test_lifecycle_emits_dataset_events() -> None:
    context = build_pipeline_context()
    lifecycle = DatasetLifecycleManager(context)
    lifecycle.emit(
        DatasetLifecycleEventType.DATASET_REGISTERED,
        dataset_id="records",
        dataset_version="1.0.0",
        correlation_id="corr-1",
        message="registered",
    )
    event_types = {event.event_type for event in lifecycle.events}
    assert DatasetLifecycleEventType.DATASET_REGISTERED in event_types


@pytest.mark.unit
def test_lifecycle_publishes_to_event_bus() -> None:
    bus = EventBus()
    context = _context_with_bus(bus)
    lifecycle = DatasetLifecycleManager(context)
    lifecycle.emit(
        DatasetLifecycleEventType.DATASET_VALIDATED,
        dataset_id=make_dataset().dataset_id,
        dataset_version="1.0.0",
        correlation_id="corr-2",
        message="validated",
    )
    assert bus.persistence.count() >= 1
    events = bus.persistence.list_events()
    assert events[0].payload["source"] == "data"


@pytest.mark.unit
def test_lifecycle_off_event() -> None:
    context = build_pipeline_context()
    lifecycle = DatasetLifecycleManager(context)
    seen: list[str] = []
    subscription = lifecycle.on_event(lambda event: seen.append(event.event_type.value))
    lifecycle.off_event(subscription)
    lifecycle.emit(
        DatasetLifecycleEventType.DATASET_LOAD_STARTED,
        dataset_id="records",
        dataset_version="1.0.0",
        correlation_id="corr-3",
        message="loading",
    )
    assert seen == []
