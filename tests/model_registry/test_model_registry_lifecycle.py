"""Unit tests for registry lifecycle."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from model_registry import RegistryLifecycleEventType, RegistryLifecycleManager


@pytest.mark.unit
def test_lifecycle_model_registered() -> None:
    lifecycle = RegistryLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_model_registered(
        model_id="model-1",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    assert lifecycle.events[0].event_type == RegistryLifecycleEventType.MODEL_REGISTERED


@pytest.mark.unit
def test_lifecycle_promotion_events() -> None:
    lifecycle = RegistryLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_promotion_requested(
        model_id="model-1",
        version_id="version-1",
        to_stage="approved",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    lifecycle.emit_promotion_approved(
        model_id="model-1",
        version_id="version-1",
        to_stage="approved",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    assert len(lifecycle.events) == 2
