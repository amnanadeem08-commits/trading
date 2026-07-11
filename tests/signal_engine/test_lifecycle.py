"""Unit/integration tests for signal lifecycle validate → register → emit."""

from __future__ import annotations

import pytest

from audit import AuditLogger, InMemoryAuditStore
from events import EventBus, EventType, InMemoryEventPersistenceStore, reset_event_bus
from models.decision import DecisionSource, DecisionState
from models.events import PredictionCreatedEvent
from models.signal import ExplainableSignal
from signal_engine import (
    SignalAssembler,
    SignalLifecycleService,
    SignalRegistry,
    SignalValidationError,
)
from tests.signal_helpers import make_assembly_request, make_reproducibility


@pytest.fixture(autouse=True)
def _reset_bus() -> None:
    reset_event_bus()
    yield
    reset_event_bus()


def _rejected_signal() -> ExplainableSignal:
    base = SignalAssembler().assemble(make_assembly_request())
    return ExplainableSignal.model_construct(
        signal_id="sig-reject",
        symbol_id=base.symbol_id,
        market_id=base.market_id,
        decision=DecisionState.SELL,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        indicators_used=base.indicators_used,
        indicator_values=base.indicator_values,
        ml_prediction=None,
        llm_insight=None,
        confidence=0.0,
        risk_assessment=base.risk_assessment,
        invalidation=base.invalidation,
        alternative_scenario=base.alternative_scenario,
        provenance=base.provenance,
        reproducibility=make_reproducibility(),
    )


@pytest.mark.unit
def test_lifecycle_accept_emits_prediction_created_and_audit() -> None:
    store = InMemoryEventPersistenceStore()
    bus = EventBus(persistence=store)
    audit_store = InMemoryAuditStore()
    registry = SignalRegistry()
    service = SignalLifecycleService(
        registry=registry,
        event_bus=bus,
        audit_logger=AuditLogger(audit_store),
    )
    received: list[str] = []
    bus.subscribe(
        EventType.PREDICTION_CREATED,
        lambda event: received.append(event.event_id),
    )

    record = service.assemble_and_register(make_assembly_request(signal_id="sig-ok"))
    assert record.signal_id == "sig-ok"
    assert registry.size == 1
    assert len(received) == 1
    assert store.count() == 1
    persisted = store.list_events()[0]
    assert isinstance(persisted, PredictionCreatedEvent)
    assert persisted.signal_id == "sig-ok"
    assert persisted.payload.get("lifecycle_state") == "accepted"
    audits = audit_store.read(market_id="crypto:binance")
    assert len(audits) == 1
    assert audits[0].event_id == persisted.event_id


@pytest.mark.unit
def test_lifecycle_reject_is_explicit_and_does_not_register() -> None:
    store = InMemoryEventPersistenceStore()
    bus = EventBus(persistence=store)
    registry = SignalRegistry()
    service = SignalLifecycleService(registry=registry, event_bus=bus)

    with pytest.raises(SignalValidationError, match="rejected") as err:
        service.register_signal(_rejected_signal())

    assert err.value.reasons
    assert any("confidence > 0" in reason for reason in err.value.reasons)
    assert registry.size == 0
    assert store.count() == 1
    rejected = store.list_events()[0]
    assert rejected.event_type == EventType.VALIDATION_COMPLETED
    assert rejected.payload["passed"] is False
    assert rejected.payload["lifecycle_state"] == "rejected"
