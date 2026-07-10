"""Unit tests for in-process event bus."""

from __future__ import annotations

import pytest

from events import (
    EventBus,
    EventBusError,
    EventPublisher,
    EventReplayer,
    EventSubscriber,
    EventType,
    InMemoryEventPersistenceStore,
    get_event_bus,
    reset_event_bus,
)
from models.common import ReproducibilityKey
from models.decision import DecisionSource, DecisionState
from models.events import PredictionCreatedEvent


def _prediction_event(correlation_id: str = "corr-1") -> PredictionCreatedEvent:
    return PredictionCreatedEvent(
        market_id="crypto:binance",
        symbol_id="BTC/USDT",
        correlation_id=correlation_id,
        signal_id="sig-1",
        decision=DecisionState.HOLD,
        decision_source=DecisionSource.ML_ONLY,
        confidence=0.5,
        reproducibility=ReproducibilityKey(
            feature_snapshot_version="fs-1",
            model_version="ml-1",
            prompt_version="prompt-1",
            strategy_version="strategy-1",
            schema_version="1.0.0",
            config_hash="hash-1",
        ),
    )


@pytest.fixture(autouse=True)
def _reset_bus() -> None:
    reset_event_bus()
    yield
    reset_event_bus()


@pytest.mark.unit
def test_publish_subscribe_and_persist() -> None:
    store = InMemoryEventPersistenceStore()
    bus = EventBus(persistence=store)
    received: list[str] = []

    bus.subscribe(EventType.PREDICTION_CREATED, lambda event: received.append(event.event_id))
    event = _prediction_event()
    bus.publish(event)

    assert received == [event.event_id]
    assert store.count() == 1


@pytest.mark.unit
def test_unsubscribe() -> None:
    bus = EventBus()
    received: list[str] = []

    subscription_id = bus.subscribe(
        EventType.PREDICTION_CREATED,
        lambda event: received.append(event.event_id),
    )
    bus.unsubscribe(subscription_id)
    bus.publish(_prediction_event())

    assert received == []


@pytest.mark.unit
def test_unsubscribe_missing_raises() -> None:
    bus = EventBus()
    with pytest.raises(EventBusError):
        bus.unsubscribe("missing")


@pytest.mark.unit
def test_event_replayer_replays_persisted_events() -> None:
    store = InMemoryEventPersistenceStore()
    bus = EventBus(persistence=store)
    event = _prediction_event(correlation_id="corr-replay")
    bus.publish(event)

    replayed: list[str] = []
    replayer = EventReplayer(store)
    count = replayer.replay(
        lambda item: replayed.append(item.correlation_id),
        correlation_id="corr-replay",
    )

    assert count == 1
    assert replayed == ["corr-replay"]


@pytest.mark.unit
def test_publisher_and_subscriber_wrappers() -> None:
    bus = EventBus()
    publisher = EventPublisher(bus)
    subscriber = EventSubscriber(bus)
    received: list[str] = []

    subscription_id = subscriber.subscribe(
        EventType.PREDICTION_CREATED,
        lambda event: received.append(event.signal_id),
    )
    event = _prediction_event()
    publisher.publish(event)
    subscriber.unsubscribe(subscription_id)

    assert received == ["sig-1"]


@pytest.mark.unit
def test_get_event_bus_singleton() -> None:
    first = get_event_bus()
    second = get_event_bus()
    assert first is second
