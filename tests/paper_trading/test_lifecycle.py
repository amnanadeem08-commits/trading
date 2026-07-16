"""PAPER-005 lifecycle events + deterministic audit records (paper_trading)."""

from __future__ import annotations

import pytest

from audit import AuditLogger, InMemoryAuditStore
from events import EventBus, InMemoryEventPersistenceStore
from models.common import utc_now
from models.decision import DecisionState
from models.risk import RiskVerdictStatus
from paper_trading import (
    FillConfig,
    PaperRiskRejectedError,
    PaperTradingOrchestrator,
    build_paper_risk_verdict,
)
from paper_trading.fill.executor import SimulatedFillExecutor
from paper_trading.ledger import PnLLedger, PositionLedger
from paper_trading.lifecycle import (
    PaperTradingLifecycleService,
    set_default_paper_lifecycle_service,
)
from paper_trading.portfolio import PaperPortfolioManager
from signal_engine import SignalAssembler
from tests.signal_helpers import make_assembly_request


@pytest.fixture(autouse=True)
def _reset() -> None:
    from paper_trading import reset_paper_registry, reset_pnl_ledger, reset_position_ledger

    reset_paper_registry()
    reset_position_ledger()
    reset_pnl_ledger()
    yield
    reset_paper_registry()
    reset_position_ledger()
    reset_pnl_ledger()


def _priced_buy(signal_id: str = "sig-lc-buy"):
    return SignalAssembler().assemble(
        make_assembly_request(
            signal_id=signal_id,
            decision=DecisionState.BUY,
            confidence=0.65,
            indicator_values={"rsi_14": 42.0, "close": 100.0},
        )
    )


@pytest.mark.integration
def test_emit_on_fill_accepted_writes_events_and_audit_and_is_idempotent() -> None:
    event_store = InMemoryEventPersistenceStore()
    bus = EventBus(persistence=event_store)
    audit_store = InMemoryAuditStore()
    audit_logger = AuditLogger(audit_store)
    service = PaperTradingLifecycleService(event_bus=bus, audit_logger=audit_logger)
    set_default_paper_lifecycle_service(service)

    signal = _priced_buy("sig-lc-ok")
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED)
    cfg = FillConfig(initial_cash=100_000.0)
    orchestrator = PaperTradingOrchestrator(
        fill_executor=SimulatedFillExecutor(config=cfg),
    )

    ts = utc_now()
    result = orchestrator.execute_simulated_fill(
        signal,
        session_id="ps-lc-accepted-1",
        verdict=verdict,
        fill_timestamp=ts,
        quantity=2.0,
    )

    events = event_store.list_events()
    assert len(events) == 2
    lifecycle_statuses = {e.payload["lifecycle_status"] for e in events}
    assert lifecycle_statuses == {"filled", "position_opened"}

    audits = audit_store.read(market_id=signal.market_id)
    assert len(audits) == 2
    audit_event_ids = {a.event_id for a in audits}
    assert audit_event_ids == {e.event_id for e in events}

    before_events = event_store.count()
    before_audits = audit_store.count()
    service.emit_fill_accepted(signal=signal, result=result)
    assert event_store.count() == before_events
    assert audit_store.count() == before_audits


@pytest.mark.integration
def test_emit_on_reject_emits_fill_rejected_and_does_not_mutate_ledgers() -> None:
    event_store = InMemoryEventPersistenceStore()
    bus = EventBus(persistence=event_store)
    audit_store = InMemoryAuditStore()
    audit_logger = AuditLogger(audit_store)
    service = PaperTradingLifecycleService(event_bus=bus, audit_logger=audit_logger)
    set_default_paper_lifecycle_service(service)

    signal = _priced_buy("sig-lc-reject")
    verdict = build_paper_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="position_limit",
    )

    cfg = FillConfig(initial_cash=100_000.0)
    position_ledger = PositionLedger()
    pnl_ledger = PnLLedger()
    portfolio_manager = PaperPortfolioManager(
        config=cfg,
        position_ledger=position_ledger,
        pnl_ledger=pnl_ledger,
    )
    fill_executor = SimulatedFillExecutor(config=cfg, portfolio_manager=portfolio_manager)

    orchestrator = PaperTradingOrchestrator(fill_executor=fill_executor)

    ts = utc_now()
    with pytest.raises(PaperRiskRejectedError):
        orchestrator.execute_simulated_fill(
            signal,
            session_id="ps-lc-rejected-1",
            verdict=verdict,
            fill_timestamp=ts,
        )

    events = event_store.list_events()
    assert len(events) == 2
    lifecycle_statuses = {e.payload["lifecycle_status"] for e in events}
    assert lifecycle_statuses == {"fill_rejected", "lifecycle_failure"}

    audits = audit_store.read(market_id=signal.market_id)
    assert len(audits) == 2

    assert len(position_ledger.entries()) == 0
    assert len(pnl_ledger.entries()) == 0
