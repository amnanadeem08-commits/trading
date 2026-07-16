"""PAPER-006 journal and review contracts (paper_trading)."""

from __future__ import annotations

import pytest

from audit import AuditLogger, InMemoryAuditStore
from events import EventBus, InMemoryEventPersistenceStore
from models.common import utc_now
from models.decision import DecisionState
from models.risk import RiskVerdictStatus
from paper_trading import (
    FillConfig,
    PaperJournalFilter,
    PaperJournalService,
    PaperJournalStore,
    PaperJournalTradeState,
    PaperOrchestrationRequest,
    PaperRiskRejectedError,
    PaperSessionStatus,
    PaperTradingOrchestrator,
    build_paper_risk_verdict,
    reset_paper_journal_store,
    reset_paper_registry,
    reset_pnl_ledger,
    reset_position_ledger,
    set_default_paper_journal_service,
)
from paper_trading.fill.executor import SimulatedFillExecutor
from paper_trading.lifecycle import (
    PaperTradingLifecycleService,
    set_default_paper_lifecycle_service,
)
from signal_engine import SignalAssembler
from tests.signal_helpers import make_assembly_request


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_paper_registry()
    reset_position_ledger()
    reset_pnl_ledger()
    reset_paper_journal_store()
    set_default_paper_lifecycle_service(None)
    set_default_paper_journal_service(None)
    yield
    reset_paper_registry()
    reset_position_ledger()
    reset_pnl_ledger()
    reset_paper_journal_store()
    set_default_paper_lifecycle_service(None)
    set_default_paper_journal_service(None)


def _priced_buy(signal_id: str = "sig-jr-buy"):
    return SignalAssembler().assemble(
        make_assembly_request(
            signal_id=signal_id,
            decision=DecisionState.BUY,
            confidence=0.65,
            indicator_values={"rsi_14": 42.0, "close": 100.0},
        )
    )


def _priced_sell(signal_id: str = "sig-jr-sell"):
    return SignalAssembler().assemble(
        make_assembly_request(
            signal_id=signal_id,
            decision=DecisionState.SELL,
            confidence=0.65,
            indicator_values={"rsi_14": 58.0, "close": 105.0},
        )
    )


def _orchestrator_with_journal() -> tuple[PaperTradingOrchestrator, PaperJournalService]:
    store = PaperJournalStore()
    journal = PaperJournalService(store=store)
    set_default_paper_journal_service(journal)
    event_store = InMemoryEventPersistenceStore()
    bus = EventBus(persistence=event_store)
    audit_store = InMemoryAuditStore()
    audit_logger = AuditLogger(audit_store)
    lifecycle = PaperTradingLifecycleService(event_bus=bus, audit_logger=audit_logger)
    set_default_paper_lifecycle_service(lifecycle)
    cfg = FillConfig(initial_cash=100_000.0)
    orchestrator = PaperTradingOrchestrator(
        fill_executor=SimulatedFillExecutor(config=cfg),
    )
    return orchestrator, journal


@pytest.mark.unit
def test_journal_entry_on_fill_links_ids_and_pnl() -> None:
    orchestrator, journal = _orchestrator_with_journal()
    signal = _priced_buy("sig-jr-fill")
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED)
    ts = utc_now()

    result = orchestrator.execute_simulated_fill(
        signal,
        session_id="ps-jr-fill-1",
        verdict=verdict,
        fill_timestamp=ts,
        quantity=2.0,
    )

    entries = journal.get_by_session("ps-jr-fill-1")
    assert len(entries) == 1
    entry = entries[0]
    assert entry.trade_state == PaperJournalTradeState.OPEN
    assert entry.signal_id == signal.signal_id
    assert entry.fill_id == result.fill.fill_id
    assert entry.position_id == result.position_entry.position_id
    assert entry.symbol_id == signal.symbol_id
    assert entry.direction == DecisionState.BUY
    assert entry.commission > 0
    assert entry.fees > 0
    assert entry.risk_gate_passed is True
    assert entry.lifecycle_status == PaperSessionStatus.FILLED.value


@pytest.mark.unit
def test_journal_entry_on_closed_position() -> None:
    orchestrator, journal = _orchestrator_with_journal()
    buy = _priced_buy("sig-jr-open")
    sell = _priced_sell("sig-jr-close")
    verdict = build_paper_risk_verdict(buy, status=RiskVerdictStatus.APPROVED)
    ts = utc_now()

    orchestrator.execute_simulated_fill(
        buy,
        session_id="ps-jr-open",
        verdict=verdict,
        fill_timestamp=ts,
        quantity=2.0,
    )
    sell_verdict = build_paper_risk_verdict(sell, status=RiskVerdictStatus.APPROVED)
    orchestrator.execute_simulated_fill(
        sell,
        session_id="ps-jr-close",
        verdict=sell_verdict,
        fill_timestamp=ts,
        quantity=2.0,
    )

    closed = journal.list_entries(
        journal_filter=PaperJournalFilter(trade_state=PaperJournalTradeState.CLOSED),
    )
    assert len(closed) == 1
    entry = closed[0]
    assert entry.trade_state == PaperJournalTradeState.CLOSED
    assert entry.position_id is not None
    assert entry.exit_price is not None
    assert entry.realized_pnl != 0.0


@pytest.mark.unit
def test_journal_entry_on_reject_does_not_duplicate_on_retry() -> None:
    orchestrator, journal = _orchestrator_with_journal()
    signal = _priced_buy("sig-jr-reject")
    verdict = build_paper_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="position_limit",
    )
    ts = utc_now()

    with pytest.raises(PaperRiskRejectedError):
        orchestrator.execute_simulated_fill(
            signal,
            session_id="ps-jr-reject",
            verdict=verdict,
            fill_timestamp=ts,
        )
    with pytest.raises(PaperRiskRejectedError):
        orchestrator.execute_simulated_fill(
            signal,
            session_id="ps-jr-reject",
            verdict=verdict,
            fill_timestamp=ts,
        )

    entries = journal.get_by_signal("sig-jr-reject")
    assert len(entries) == 1
    assert entries[0].trade_state == PaperJournalTradeState.REJECTED
    assert entries[0].risk_gate_passed is False
    assert entries[0].fill_id is None


@pytest.mark.unit
def test_journal_entry_on_cancel() -> None:
    orchestrator, journal = _orchestrator_with_journal()
    signal = _priced_buy("sig-jr-cancel")
    orchestrator.prepare(
        PaperOrchestrationRequest(session_id="ps-jr-cancel", signal=signal),
    )
    orchestrator.cancel_session_from_signal(
        signal=signal,
        session_id="ps-jr-cancel",
        reason="user cancelled",
    )

    entries = journal.get_by_session("ps-jr-cancel")
    assert len(entries) == 1
    assert entries[0].trade_state == PaperJournalTradeState.CANCELLED
    assert entries[0].validation_outcome == "cancelled"


@pytest.mark.unit
def test_attach_review_note_and_lookup_by_signal() -> None:
    orchestrator, journal = _orchestrator_with_journal()
    signal = _priced_buy("sig-jr-review")
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED)
    orchestrator.execute_simulated_fill(
        signal,
        session_id="ps-jr-review",
        verdict=verdict,
        quantity=1.0,
    )
    entry = journal.get_by_signal("sig-jr-review")[0]
    review = journal.attach_review(
        journal_id=entry.journal_id,
        tags=("discipline", "sizing"),
        lesson="Wait for confirmation",
        notes="Simulated review only — not financial advice",
    )
    assert review.journal_id == entry.journal_id
    reviews = journal.list_reviews(entry.journal_id)
    assert len(reviews) == 1
    assert reviews[0].tags == ("discipline", "sizing")


@pytest.mark.unit
def test_journal_filter_and_summary() -> None:
    orchestrator, journal = _orchestrator_with_journal()
    buy = _priced_buy("sig-jr-sum-buy")
    reject = _priced_buy("sig-jr-sum-reject")
    approved = build_paper_risk_verdict(buy, status=RiskVerdictStatus.APPROVED)
    rejected = build_paper_risk_verdict(
        reject,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="limit",
    )

    orchestrator.execute_simulated_fill(
        buy,
        session_id="ps-jr-sum-ok",
        verdict=approved,
        quantity=1.0,
    )
    with pytest.raises(PaperRiskRejectedError):
        orchestrator.execute_simulated_fill(
            reject,
            session_id="ps-jr-sum-bad",
            verdict=rejected,
        )

    summary = journal.summarize()
    assert summary.total_entries == 2
    assert summary.open_count == 1
    assert summary.rejected_count == 1
    assert buy.symbol_id in summary.symbol_ids

    filtered = journal.list_entries(
        journal_filter=PaperJournalFilter(
            symbol_id=buy.symbol_id,
            trade_state=PaperJournalTradeState.OPEN,
        ),
    )
    assert len(filtered) == 1


@pytest.mark.unit
def test_fill_idempotent_journal_on_orchestrator_retry() -> None:
    orchestrator, journal = _orchestrator_with_journal()
    signal = _priced_buy("sig-jr-idem")
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED)
    ts = utc_now()
    kwargs = {
        "session_id": "ps-jr-idem",
        "verdict": verdict,
        "fill_timestamp": ts,
        "quantity": 1.0,
    }
    first = orchestrator.execute_simulated_fill(signal, **kwargs)
    before = journal.store.size
    service = journal
    service.record_fill_accepted(signal=signal, result=first)
    assert journal.store.size == before
    assert (
        journal.get_by_session("ps-jr-idem")[0].journal_id
        == service.get_by_session(
            "ps-jr-idem",
        )[0].journal_id
    )


@pytest.mark.unit
def test_prepare_with_risk_gate_records_rejected_journal() -> None:
    orchestrator, journal = _orchestrator_with_journal()
    signal = _priced_buy("sig-jr-prep-reject")
    verdict = build_paper_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="exposure",
    )
    result = orchestrator.prepare_with_risk_gate(
        signal,
        session_id="ps-jr-prep-reject",
        verdict=verdict,
    )
    assert result.status == PaperSessionStatus.RISK_REJECTED
    entries = journal.get_by_session("ps-jr-prep-reject")
    assert len(entries) == 1
    assert entries[0].trade_state == PaperJournalTradeState.REJECTED
