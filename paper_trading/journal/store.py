"""Append-only in-memory journal store (PAPER-006 stub)."""

from __future__ import annotations

from threading import RLock

from paper_trading.contracts.journal import (
    PaperJournalEntry,
    PaperJournalFilter,
    PaperJournalReviewNote,
    PaperJournalSummary,
    PaperJournalTradeState,
)
from paper_trading.exceptions import PaperJournalNotFoundError


class PaperJournalStore:
    """Thread-safe, append-only journal store with idempotent entry recording."""

    def __init__(self, *, max_entries: int = 50_000) -> None:
        if max_entries < 1:
            msg = "max_entries must be >= 1"
            raise ValueError(msg)
        self._lock = RLock()
        self._max_entries = max_entries
        self._entries: list[PaperJournalEntry] = []
        self._entries_by_id: dict[str, PaperJournalEntry] = {}
        self._reviews: list[PaperJournalReviewNote] = []
        self._reviews_by_journal: dict[str, list[PaperJournalReviewNote]] = {}

    def append(self, entry: PaperJournalEntry) -> PaperJournalEntry:
        """Append a journal entry; return existing entry when journal_id already recorded."""
        with self._lock:
            existing = self._entries_by_id.get(entry.journal_id)
            if existing is not None:
                return existing
            if len(self._entries) >= self._max_entries:
                msg = f"Paper journal store capacity exceeded: {self._max_entries}"
                raise ValueError(msg)
            self._entries.append(entry)
            self._entries_by_id[entry.journal_id] = entry
            return entry

    def append_review(self, review: PaperJournalReviewNote) -> PaperJournalReviewNote:
        """Append a review note linked to an existing journal entry."""
        with self._lock:
            if review.journal_id not in self._entries_by_id:
                raise PaperJournalNotFoundError(review.journal_id)
            for existing in self._reviews_by_journal.get(review.journal_id, ()):
                if existing.review_id == review.review_id:
                    return existing
            self._reviews.append(review)
            bucket = self._reviews_by_journal.setdefault(review.journal_id, [])
            bucket.append(review)
            return review

    def get(self, journal_id: str) -> PaperJournalEntry:
        with self._lock:
            entry = self._entries_by_id.get(journal_id)
            if entry is None:
                raise PaperJournalNotFoundError(journal_id)
            return entry

    def get_by_session(self, session_id: str) -> tuple[PaperJournalEntry, ...]:
        with self._lock:
            return tuple(e for e in self._entries if e.session_id == session_id)

    def get_by_signal(self, signal_id: str) -> tuple[PaperJournalEntry, ...]:
        with self._lock:
            return tuple(e for e in self._entries if e.signal_id == signal_id)

    def list_entries(
        self,
        *,
        journal_filter: PaperJournalFilter | None = None,
    ) -> tuple[PaperJournalEntry, ...]:
        with self._lock:
            entries = self._entries
            if journal_filter is None:
                return tuple(entries)
            return tuple(e for e in entries if _matches_filter(e, journal_filter))

    def list_reviews(self, journal_id: str) -> tuple[PaperJournalReviewNote, ...]:
        with self._lock:
            return tuple(self._reviews_by_journal.get(journal_id, ()))

    def summarize(
        self,
        *,
        journal_filter: PaperJournalFilter | None = None,
    ) -> PaperJournalSummary:
        entries = self.list_entries(journal_filter=journal_filter)
        rejected = sum(1 for e in entries if e.trade_state == PaperJournalTradeState.REJECTED)
        cancelled = sum(1 for e in entries if e.trade_state == PaperJournalTradeState.CANCELLED)
        open_count = sum(1 for e in entries if e.trade_state == PaperJournalTradeState.OPEN)
        closed = sum(1 for e in entries if e.trade_state == PaperJournalTradeState.CLOSED)
        symbols = tuple(sorted({e.symbol_id for e in entries}))
        return PaperJournalSummary(
            total_entries=len(entries),
            rejected_count=rejected,
            cancelled_count=cancelled,
            open_count=open_count,
            closed_count=closed,
            total_realized_pnl=sum(e.realized_pnl for e in entries),
            total_unrealized_pnl=sum(e.unrealized_pnl for e in entries),
            total_commission=sum(e.commission for e in entries),
            total_fees=sum(e.fees for e in entries),
            symbol_ids=symbols,
        )

    def entries(self) -> tuple[PaperJournalEntry, ...]:
        with self._lock:
            return tuple(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._entries_by_id.clear()
            self._reviews.clear()
            self._reviews_by_journal.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._entries)


def _matches_filter(entry: PaperJournalEntry, journal_filter: PaperJournalFilter) -> bool:
    if journal_filter.session_id is not None and entry.session_id != journal_filter.session_id:
        return False
    if journal_filter.signal_id is not None and entry.signal_id != journal_filter.signal_id:
        return False
    if journal_filter.fill_id is not None and entry.fill_id != journal_filter.fill_id:
        return False
    if journal_filter.position_id is not None and entry.position_id != journal_filter.position_id:
        return False
    if journal_filter.symbol_id is not None and entry.symbol_id != journal_filter.symbol_id:
        return False
    if journal_filter.market_id is not None and entry.market_id != journal_filter.market_id:
        return False
    if journal_filter.timeframe is not None and entry.timeframe != journal_filter.timeframe:
        return False
    if journal_filter.trade_state is not None and entry.trade_state != journal_filter.trade_state:
        return False
    return not (
        journal_filter.direction is not None and entry.direction != journal_filter.direction
    )


_default_journal_store: PaperJournalStore | None = None
_store_lock = RLock()


def get_paper_journal_store() -> PaperJournalStore:
    global _default_journal_store
    with _store_lock:
        if _default_journal_store is None:
            _default_journal_store = PaperJournalStore()
        return _default_journal_store


def reset_paper_journal_store() -> None:
    global _default_journal_store
    with _store_lock:
        _default_journal_store = None
