"""Unit tests for pipeline lifecycle and cancellation."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from pipeline import (
    CancellationToken,
    PipelineBuilder,
    PipelineExecutor,
    PipelineLifecycleEventType,
    PipelineStatus,
    build_pipeline_context,
)
from pipeline.context import PipelineContext
from services import reset_application_context
from services.context import ApplicationContext, build_application_context
from tests.pipeline_fixtures import IngestStage
from tests.pipeline_helpers import make_pipeline_request


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
def test_lifecycle_emits_pipeline_events() -> None:
    context = build_pipeline_context()
    pipeline = PipelineBuilder("lifecycle").add_stage(IngestStage()).build()
    executor = PipelineExecutor(context)
    executor.execute(pipeline, make_pipeline_request())
    event_types = {event.event_type for event in executor.lifecycle.events}
    assert PipelineLifecycleEventType.PIPELINE_STARTED in event_types
    assert PipelineLifecycleEventType.STAGE_STARTED in event_types
    assert PipelineLifecycleEventType.STAGE_COMPLETED in event_types
    assert PipelineLifecycleEventType.PIPELINE_COMPLETED in event_types


@pytest.mark.unit
def test_lifecycle_publishes_to_event_bus() -> None:
    bus = EventBus()
    context = _context_with_bus(bus)
    pipeline = PipelineBuilder("bus").add_stage(IngestStage()).build()
    executor = PipelineExecutor(context)
    executor.execute(pipeline, make_pipeline_request())
    assert bus.persistence.count() >= 1
    events = bus.persistence.list_events()
    assert events[0].payload["source"] == "pipeline"


@pytest.mark.unit
def test_cancellation_token_stops_pipeline() -> None:
    context = build_pipeline_context()
    pipeline = PipelineBuilder("cancel").add_stage(IngestStage()).build()
    token = CancellationToken()
    token.cancel()
    executor = PipelineExecutor(context)
    response = executor.execute(pipeline, make_pipeline_request(), cancellation=token)
    assert response.result.status == PipelineStatus.CANCELLED


@pytest.mark.unit
def test_graceful_shutdown_stops_before_next_stage() -> None:
    context = build_pipeline_context()
    ingest = IngestStage()

    class _Second(IngestStage):
        def name(self) -> str:
            return "second"

        def dependencies(self) -> tuple[str, ...]:
            return ("ingest",)

    pipeline = PipelineBuilder("shutdown").add_stage(ingest).add_stage(_Second()).build()
    pipeline.request_shutdown()
    executor = PipelineExecutor(context)
    response = executor.execute(pipeline, make_pipeline_request())
    assert response.result.status == PipelineStatus.COMPLETED
    assert len(response.result.stage_results) == 1
    assert any("shutdown requested" in warning for warning in response.result.warnings)
