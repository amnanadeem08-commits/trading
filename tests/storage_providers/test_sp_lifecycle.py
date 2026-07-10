"""Unit tests for provider lifecycle."""

from __future__ import annotations

import pytest

from events.event_bus import EventBus
from metrics.registry import MetricRegistry
from storage_providers import ProviderLifecycleEventType, ProviderLifecycleManager
from tests.storage_providers_helpers import STUB_PROVIDER_ID


@pytest.mark.unit
def test_provider_lifecycle_emits_registered_event() -> None:
    lifecycle = ProviderLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    lifecycle.emit_provider_registered(
        provider_id=STUB_PROVIDER_ID,
        name="Stub Provider",
        version="1.0.0",
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    assert lifecycle.events[-1].event_type == ProviderLifecycleEventType.PROVIDER_REGISTERED


@pytest.mark.unit
def test_provider_lifecycle_handler_subscription() -> None:
    lifecycle = ProviderLifecycleManager(event_bus=EventBus(), metrics=MetricRegistry())
    received: list[str] = []

    def handler(event: object) -> None:
        from storage_providers import ProviderLifecycleEvent

        assert isinstance(event, ProviderLifecycleEvent)
        received.append(event.provider_id)

    subscription_id = lifecycle.on_event(handler)
    lifecycle.emit_provider_validated(
        provider_id=STUB_PROVIDER_ID,
        correlation_id="corr-1",
        trace_id="trace-1",
    )
    lifecycle.off_event(subscription_id)
    assert received == [STUB_PROVIDER_ID]
