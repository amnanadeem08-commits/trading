"""Append-only position ledger."""

from __future__ import annotations

from threading import RLock

from paper_trading.contracts.ledger import PositionLedgerEntry, PositionStatus


class PositionLedger:
    """Append-only position ledger (no updates/deletes)."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: list[PositionLedgerEntry] = []

    def append(self, entry: PositionLedgerEntry) -> PositionLedgerEntry:
        with self._lock:
            self._entries.append(entry)
            return entry

    def entries(self) -> tuple[PositionLedgerEntry, ...]:
        with self._lock:
            return tuple(self._entries)

    def open_for_symbol(self, symbol: str) -> PositionLedgerEntry | None:
        with self._lock:
            for entry in reversed(self._entries):
                if entry.symbol == symbol and entry.status == PositionStatus.OPEN:
                    return entry
            return None

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_default_position_ledger: PositionLedger | None = None
_ledger_lock = RLock()


def get_position_ledger() -> PositionLedger:
    global _default_position_ledger
    with _ledger_lock:
        if _default_position_ledger is None:
            _default_position_ledger = PositionLedger()
        return _default_position_ledger


def reset_position_ledger() -> None:
    global _default_position_ledger
    with _ledger_lock:
        _default_position_ledger = None
