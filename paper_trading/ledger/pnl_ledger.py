"""Append-only PnL ledger."""

from __future__ import annotations

from threading import RLock

from paper_trading.contracts.ledger import PnLLedgerEntry


class PnLLedger:
    """Append-only PnL ledger (no updates/deletes)."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: list[PnLLedgerEntry] = []

    def append(self, entry: PnLLedgerEntry) -> PnLLedgerEntry:
        with self._lock:
            self._entries.append(entry)
            return entry

    def entries(self) -> tuple[PnLLedgerEntry, ...]:
        with self._lock:
            return tuple(self._entries)

    def last(self) -> PnLLedgerEntry | None:
        with self._lock:
            return self._entries[-1] if self._entries else None

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_default_pnl_ledger: PnLLedger | None = None
_ledger_lock = RLock()


def get_pnl_ledger() -> PnLLedger:
    global _default_pnl_ledger
    with _ledger_lock:
        if _default_pnl_ledger is None:
            _default_pnl_ledger = PnLLedger()
        return _default_pnl_ledger


def reset_pnl_ledger() -> None:
    global _default_pnl_ledger
    with _ledger_lock:
        _default_pnl_ledger = None
