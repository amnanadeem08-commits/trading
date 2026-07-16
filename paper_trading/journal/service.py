"""Build journal entries from paper execution outcomes (PAPER-006)."""

from __future__ import annotations

import hashlib

from legacy_config import TIMEFRAME
from models.common import UTCDateTime
from models.signal import ExplainableSignal
from paper_trading.contracts.journal import (
    PaperJournalEntry,
    PaperJournalFilter,
    PaperJournalReviewNote,
    PaperJournalSummary,
    PaperJournalTradeState,
    PaperPerformanceMetrics,
)
from paper_trading.contracts.ledger import PositionStatus
from paper_trading.contracts.paper_fill import PaperFillResult
from paper_trading.contracts.paper_request import PaperSessionStatus
from paper_trading.contracts.paper_risk import PaperRiskGateResult
from paper_trading.journal.metrics import compute_performance_metrics
from paper_trading.journal.store import PaperJournalStore, get_paper_journal_store
from paper_trading.ledger.pnl_ledger import PnLLedger, get_pnl_ledger


def _target_price_from_signal(signal: ExplainableSignal) -> float | None:
    for key in ("target", "resistance", "take_profit"):
        value = signal.indicator_values.get(key)
        if isinstance(value, (int, float)) and float(value) > 0:
            return float(value)
    return None


def _deterministic_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _journal_id_for_outcome(
    *,
    session_id: str,
    signal_id: str,
    trade_state: PaperJournalTradeState,
    fill_id: str | None,
) -> str:
    return _deterministic_id(
        "paper-journal",
        session_id,
        signal_id,
        trade_state.value,
        fill_id or "",
    )


def _trade_state_from_fill(result: PaperFillResult) -> PaperJournalTradeState:
    if result.position_entry.status == PositionStatus.CLOSED:
        return PaperJournalTradeState.CLOSED
    return PaperJournalTradeState.OPEN


class PaperJournalService:
    """Record and query paper trade journal entries without duplicating ledger logic."""

    def __init__(self, *, store: PaperJournalStore | None = None) -> None:
        self._store = store if store is not None else get_paper_journal_store()

    @property
    def store(self) -> PaperJournalStore:
        return self._store

    def record_fill_accepted(
        self,
        *,
        signal: ExplainableSignal,
        result: PaperFillResult,
        gate: PaperRiskGateResult | None = None,
    ) -> PaperJournalEntry:
        """Record a journal entry from an accepted simulated fill (PAPER-004 result)."""
        trade_state = _trade_state_from_fill(result)
        pos = result.position_entry
        fill = result.fill
        pnl = result.pnl_entry
        fees = fill.commission + fill.slippage + fill.spread
        entry_price = pos.entry_price
        exit_price = pos.fill_price if pos.status == PositionStatus.CLOSED else None

        entry = PaperJournalEntry(
            journal_id=_journal_id_for_outcome(
                session_id=result.session_id,
                signal_id=result.signal_id,
                trade_state=trade_state,
                fill_id=fill.fill_id,
            ),
            session_id=result.session_id,
            signal_id=result.signal_id,
            fill_id=fill.fill_id,
            position_id=pos.position_id,
            trade_id=fill.trade_id,
            symbol_id=result.symbol_id,
            market_id=result.market_id,
            timeframe=TIMEFRAME,
            direction=result.decision,
            side=fill.side,
            trade_state=trade_state,
            lifecycle_status=result.status.value,
            session_status=result.status,
            risk_decision=signal.decision,
            risk_gate_passed=True if gate is None else gate.passed,
            risk_gate_reasons=result.risk_gate_reasons,
            recorded_at=result.created_at,
            filled_at=fill.filled_at,
            closed_at=pos.closed_at,
            entry_price=entry_price,
            exit_price=exit_price,
            fill_price=fill.fill_price,
            stop_price=signal.invalidation.price_level,
            target_price=_target_price_from_signal(signal),
            commission=fill.commission,
            slippage=fill.slippage,
            fees=fees,
            realized_pnl=pnl.realized_pnl,
            unrealized_pnl=pnl.unrealized_pnl,
            validation_outcome=None,
            explanatory_notes=result.message,
        )
        return self._store.append(entry)

    def record_fill_rejected(
        self,
        *,
        signal: ExplainableSignal,
        session_id: str,
        reason: str,
        risk_reasons: tuple[str, ...] = (),
        gate: PaperRiskGateResult | None = None,
        occurred_at: UTCDateTime,
    ) -> PaperJournalEntry:
        """Record a rejected paper attempt (PAPER-003 risk / mapping failure)."""
        entry = PaperJournalEntry(
            journal_id=_journal_id_for_outcome(
                session_id=session_id,
                signal_id=signal.signal_id,
                trade_state=PaperJournalTradeState.REJECTED,
                fill_id=None,
            ),
            session_id=session_id,
            signal_id=signal.signal_id,
            symbol_id=signal.symbol_id,
            market_id=signal.market_id,
            timeframe=TIMEFRAME,
            direction=signal.decision,
            trade_state=PaperJournalTradeState.REJECTED,
            lifecycle_status=PaperSessionStatus.REJECTED.value,
            session_status=PaperSessionStatus.REJECTED,
            risk_decision=signal.decision,
            risk_gate_passed=False if gate is None else gate.passed,
            risk_gate_reasons=risk_reasons,
            recorded_at=occurred_at,
            validation_outcome="rejected",
            explanatory_notes=reason,
        )
        return self._store.append(entry)

    def record_risk_rejected(
        self,
        *,
        signal: ExplainableSignal,
        session_id: str,
        gate: PaperRiskGateResult,
        occurred_at: UTCDateTime,
    ) -> PaperJournalEntry:
        """Record a risk-gate rejection during prepare (no fill attempted)."""
        return self.record_fill_rejected(
            signal=signal,
            session_id=session_id,
            reason=gate.message,
            risk_reasons=gate.reasons,
            gate=gate,
            occurred_at=occurred_at,
        )

    def record_cancellation(
        self,
        *,
        signal: ExplainableSignal,
        session_id: str,
        reason: str,
        occurred_at: UTCDateTime,
    ) -> PaperJournalEntry:
        """Record a cancelled paper session (PAPER-005 cancellation path)."""
        entry = PaperJournalEntry(
            journal_id=_journal_id_for_outcome(
                session_id=session_id,
                signal_id=signal.signal_id,
                trade_state=PaperJournalTradeState.CANCELLED,
                fill_id=None,
            ),
            session_id=session_id,
            signal_id=signal.signal_id,
            symbol_id=signal.symbol_id,
            market_id=signal.market_id,
            timeframe=TIMEFRAME,
            direction=signal.decision,
            trade_state=PaperJournalTradeState.CANCELLED,
            lifecycle_status=PaperSessionStatus.CANCELLED.value,
            session_status=PaperSessionStatus.CANCELLED,
            risk_decision=signal.decision,
            recorded_at=occurred_at,
            validation_outcome="cancelled",
            explanatory_notes=reason,
        )
        return self._store.append(entry)

    def attach_review(
        self,
        *,
        journal_id: str,
        tags: tuple[str, ...] = (),
        lesson: str = "",
        notes: str = "",
        created_at: UTCDateTime | None = None,
    ) -> PaperJournalReviewNote:
        """Attach an append-only post-trade review note to a journal entry."""
        from models.common import utc_now

        ts = created_at or utc_now()
        review_id = _deterministic_id(
            "paper-review",
            journal_id,
            ts.isoformat(),
            lesson,
            notes,
            "|".join(tags),
        )
        review = PaperJournalReviewNote(
            review_id=review_id,
            journal_id=journal_id,
            tags=tags,
            lesson=lesson,
            notes=notes,
            created_at=ts,
        )
        return self._store.append_review(review)

    def get(self, journal_id: str) -> PaperJournalEntry:
        return self._store.get(journal_id)

    def get_by_session(self, session_id: str) -> tuple[PaperJournalEntry, ...]:
        return self._store.get_by_session(session_id)

    def get_by_signal(self, signal_id: str) -> tuple[PaperJournalEntry, ...]:
        return self._store.get_by_signal(signal_id)

    def list_entries(
        self,
        *,
        journal_filter: PaperJournalFilter | None = None,
    ) -> tuple[PaperJournalEntry, ...]:
        return self._store.list_entries(journal_filter=journal_filter)

    def summarize(
        self,
        *,
        journal_filter: PaperJournalFilter | None = None,
    ) -> PaperJournalSummary:
        return self._store.summarize(journal_filter=journal_filter)

    def performance_metrics(
        self,
        *,
        journal_filter: PaperJournalFilter | None = None,
        pnl_ledger: PnLLedger | None = None,
    ) -> PaperPerformanceMetrics:
        """Deterministic performance metrics for dashboard/reporting (PAPER-007)."""
        entries = self.list_entries(journal_filter=journal_filter)
        ledger = pnl_ledger if pnl_ledger is not None else get_pnl_ledger()
        return compute_performance_metrics(entries, pnl_entries=ledger.entries())

    def list_reviews(self, journal_id: str) -> tuple[PaperJournalReviewNote, ...]:
        return self._store.list_reviews(journal_id)


_default_journal_service: PaperJournalService | None = None


def get_default_paper_journal_service() -> PaperJournalService:
    global _default_journal_service
    if _default_journal_service is None:
        _default_journal_service = PaperJournalService()
    return _default_journal_service


def set_default_paper_journal_service(service: PaperJournalService | None) -> None:
    """Override the default journal service (used by tests)."""
    global _default_journal_service
    _default_journal_service = service
