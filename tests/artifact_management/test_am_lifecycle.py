"""Unit tests for artifact lifecycle."""

from __future__ import annotations

import pytest

from artifact_management import ArtifactLifecycleEventType, ArtifactLifecycleManager
from events.event_bus import EventBus
from metrics.registry import MetricRegistry


@pytest.mark.unit
def test_artifact_lifecycle_emits_events() -> None:
    lifecycle = ArtifactLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_artifact_registered(
        artifact_id="artifact-1",
        name="Stub",
        version="1.0.0",
        correlation_id="corr",
        trace_id="trace",
    )
    lifecycle.emit_artifact_resolved(
        artifact_id="artifact-1",
        uri="local://artifacts/stub",
        correlation_id="corr",
        trace_id="trace",
    )
    event_types = {event.event_type for event in lifecycle.events}
    assert ArtifactLifecycleEventType.ARTIFACT_REGISTERED in event_types
    assert ArtifactLifecycleEventType.ARTIFACT_RESOLVED in event_types


@pytest.mark.unit
def test_artifact_lifecycle_all_event_types() -> None:
    lifecycle = ArtifactLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_artifact_validated(
        artifact_id="artifact-1",
        correlation_id="corr",
        trace_id="trace",
    )
    lifecycle.emit_artifact_cached(
        artifact_id="artifact-1",
        correlation_id="corr",
        trace_id="trace",
    )
    lifecycle.emit_artifact_expired(
        artifact_id="artifact-1",
        correlation_id="corr",
        trace_id="trace",
    )
    lifecycle.emit_artifact_failed(
        artifact_id="artifact-1",
        message="failed",
        correlation_id="corr",
        trace_id="trace",
    )
    event_types = {event.event_type for event in lifecycle.events}
    assert ArtifactLifecycleEventType.ARTIFACT_VALIDATED in event_types
    assert ArtifactLifecycleEventType.ARTIFACT_CACHED in event_types
    assert ArtifactLifecycleEventType.ARTIFACT_EXPIRED in event_types
    assert ArtifactLifecycleEventType.ARTIFACT_FAILED in event_types
