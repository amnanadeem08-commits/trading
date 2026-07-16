"""E2E integration: signal → risk gate → fill → ledger → lifecycle → journal → metrics."""

from __future__ import annotations

import pytest

from audit import AuditLogger, InMemoryAuditStore
from config.settings import get_settings, reset_settings
from events import EventBus, InMemoryEventPersistenceStore
from models.common import utc_now
from models.decision import DecisionState
from models.risk import RiskVerdictStatus
from models.signal import InvalidationRule
from paper_trading import (
    FillConfig,
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
def _reset_globals() -> None:
    reset_paper_registry()
    reset_position_ledger()
    reset_pnl_ledger()
    reset_paper_journal_store()
    set_default_paper_lifecycle_service(None)
    set_default_paper_journal_service(None)
    reset_settings()
    yield
    reset_paper_registry()
    reset_position_ledger()
    reset_pnl_ledger()
    reset_paper_journal_store()
    set_default_paper_lifecycle_service(None)
    set_default_paper_journal_service(None)
    reset_settings()


def _orchestrator_stack() -> tuple[PaperTradingOrchestrator, PaperJournalService, object, object]:
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
    return orchestrator, journal, event_store, audit_store


def _buy_signal(
    signal_id: str,
    *,
    close: float = 100.0,
    target: float | None = None,
    stop: float | None = None,
) -> object:
    indicators: dict[str, float] = {"rsi_14": 42.0, "close": close}
    if target is not None:
        indicators["target"] = target
    invalidation = InvalidationRule(
        condition="Break below stop",
        price_level=stop,
    )
    return SignalAssembler().assemble(
        make_assembly_request(
            signal_id=signal_id,
            decision=DecisionState.BUY,
            confidence=0.65,
            indicator_values=indicators,
            invalidation=invalidation,
        )
    )


def _sell_signal(signal_id: str, *, close: float = 105.0) -> object:
    return SignalAssembler().assemble(
        make_assembly_request(
            signal_id=signal_id,
            decision=DecisionState.SELL,
            confidence=0.65,
            indicator_values={"rsi_14": 58.0, "close": close},
        )
    )


@pytest.mark.integration
def test_e2e_accepted_open_trade_full_path() -> None:
    orchestrator, journal, event_store, audit_store = _orchestrator_stack()
    signal = _buy_signal("sig-e2e-open", stop=95.0, target=115.0)
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED)
    ts = utc_now()

    result = orchestrator.execute_simulated_fill(
        signal,
        session_id="ps-e2e-open",
        verdict=verdict,
        fill_timestamp=ts,
        quantity=2.0,
    )

    assert result.status == PaperSessionStatus.FILLED
    assert orchestrator.get_session("ps-e2e-open").status == PaperSessionStatus.FILLED
    assert len(event_store.list_events()) >= 2
    assert audit_store.count() >= 2

    entries = journal.get_by_session("ps-e2e-open")
    assert len(entries) == 1
    assert entries[0].trade_state == PaperJournalTradeState.OPEN
    assert entries[0].stop_price == pytest.approx(95.0)
    assert entries[0].target_price == pytest.approx(115.0)

    metrics = journal.performance_metrics()
    assert metrics.total_simulated_trades == 1
    assert metrics.open_trades == 1
    assert metrics.closed_trades == 0


@pytest.mark.integration
def test_e2e_closed_trade_updates_metrics() -> None:
    orchestrator, journal, _, _ = _orchestrator_stack()
    buy = _buy_signal("sig-e2e-buy", close=100.0, stop=95.0, target=115.0)
    sell = _sell_signal("sig-e2e-sell", close=105.0)
    ts = utc_now()
    approved = build_paper_risk_verdict(buy, status=RiskVerdictStatus.APPROVED)

    orchestrator.execute_simulated_fill(
        buy,
        session_id="ps-e2e-buy",
        verdict=approved,
        fill_timestamp=ts,
        quantity=2.0,
    )
    sell_verdict = build_paper_risk_verdict(sell, status=RiskVerdictStatus.APPROVED)
    orchestrator.execute_simulated_fill(
        sell,
        session_id="ps-e2e-sell",
        verdict=sell_verdict,
        fill_timestamp=ts,
        quantity=2.0,
    )

    metrics = journal.performance_metrics(
        pnl_ledger=orchestrator.fill_executor.portfolio_manager.pnl_ledger,
    )
    assert metrics.open_trades == 0
    assert metrics.closed_trades == 1
    assert metrics.total_simulated_trades == 2
    assert metrics.wins + metrics.losses + metrics.breakeven_trades == metrics.closed_trades
    assert metrics.max_drawdown is not None
    assert metrics.signal_accuracy is not None


@pytest.mark.integration
def test_e2e_risk_rejected_no_ledger_mutation() -> None:
    orchestrator, journal, event_store, _ = _orchestrator_stack()
    signal = _buy_signal("sig-e2e-reject")
    verdict = build_paper_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="exposure_cap",
    )

    with pytest.raises(PaperRiskRejectedError):
        orchestrator.execute_simulated_fill(signal, session_id="ps-e2e-reject", verdict=verdict)

    assert journal.get_by_session("ps-e2e-reject")[0].trade_state == PaperJournalTradeState.REJECTED
    assert any(
        "fill_rejected" in e.payload.get("lifecycle_status", "") for e in event_store.list_events()
    )

    metrics = journal.performance_metrics()
    assert metrics.rejected_trades == 1
    assert metrics.total_simulated_trades == 0


@pytest.mark.integration
def test_e2e_cancelled_session() -> None:
    orchestrator, journal, event_store, _ = _orchestrator_stack()
    signal = _buy_signal("sig-e2e-cancel")
    orchestrator.prepare(PaperOrchestrationRequest(session_id="ps-e2e-cancel", signal=signal))
    orchestrator.cancel_session_from_signal(
        signal=signal,
        session_id="ps-e2e-cancel",
        reason="operator cancelled",
    )

    entry = journal.get_by_session("ps-e2e-cancel")[0]
    assert entry.trade_state == PaperJournalTradeState.CANCELLED
    assert orchestrator.get_session("ps-e2e-cancel").status == PaperSessionStatus.CANCELLED
    assert event_store.count() >= 1

    metrics = journal.performance_metrics()
    assert metrics.cancelled_trades == 1


@pytest.mark.integration
def test_e2e_prepare_risk_rejected_path() -> None:
    orchestrator, journal, _, _ = _orchestrator_stack()
    signal = _buy_signal("sig-e2e-prep-reject")
    verdict = build_paper_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="limit",
    )
    result = orchestrator.prepare_with_risk_gate(
        signal,
        session_id="ps-e2e-prep-reject",
        verdict=verdict,
    )
    assert result.status == PaperSessionStatus.RISK_REJECTED
    assert (
        journal.get_by_session("ps-e2e-prep-reject")[0].trade_state
        == PaperJournalTradeState.REJECTED
    )


@pytest.mark.integration
def test_live_trading_flag_remains_disabled() -> None:
    settings = get_settings()
    assert settings.feature_flags.live_trading_enabled is False
    orchestrator, _, _, _ = _orchestrator_stack()
    orchestrator.assert_paper_safe()
