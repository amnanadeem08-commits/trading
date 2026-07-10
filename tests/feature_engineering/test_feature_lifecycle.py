"""Unit tests for feature lifecycle."""

from __future__ import annotations

from events.event_bus import EventBus
from feature_engineering import FeatureLifecycleEventType, FeatureLifecycleManager
from metrics.registry import MetricRegistry


def test_lifecycle_emit_events() -> None:
    bus = EventBus()
    metrics = MetricRegistry()
    lifecycle = FeatureLifecycleManager(event_bus=bus, metrics=metrics)
    lifecycle.emit(
        FeatureLifecycleEventType.EXTRACTION_STARTED,
        dataset_id="dataset-1",
        correlation_id="corr-1",
        trace_id="trace-1",
        message="started",
    )
    assert len(lifecycle.events) == 1
    assert lifecycle.events[0].event_type == FeatureLifecycleEventType.EXTRACTION_STARTED
    assert bus.persistence.count() >= 1


def test_lifecycle_typed_events() -> None:
    bus = EventBus()
    metrics = MetricRegistry()
    lifecycle = FeatureLifecycleManager(event_bus=bus, metrics=metrics)
    started = lifecycle.emit_extraction_started(
        pipeline_id="pipeline-1",
        dataset_id="dataset-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    completed = lifecycle.emit_extraction_completed(
        pipeline_id="pipeline-1",
        dataset_id="dataset-1",
        vectors_extracted=3,
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    validation = lifecycle.emit_validation_completed(
        dataset_id="dataset-1",
        valid=True,
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    registered = lifecycle.emit_feature_registered(
        feature_id="feature-1",
        schema_id="feature-schema-v1",
        dataset_id="dataset-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    assert started.pipeline_id == "pipeline-1"
    assert completed.vectors_extracted == 3
    assert validation.valid is True
    assert registered.feature_id == "feature-1"
    assert len(lifecycle.events) == 4


def test_lifecycle_handler_subscription() -> None:
    bus = EventBus()
    metrics = MetricRegistry()
    lifecycle = FeatureLifecycleManager(event_bus=bus, metrics=metrics)
    received: list[str] = []

    def handler(event) -> None:
        received.append(event.dataset_id)

    subscription = lifecycle.on_event(handler)
    lifecycle.emit(
        FeatureLifecycleEventType.FEATURE_REGISTERED,
        dataset_id="dataset-2",
        correlation_id="corr-2",
        trace_id="trace-2",
        message="registered",
    )
    lifecycle.off_event(subscription)
    assert received == ["dataset-2"]
