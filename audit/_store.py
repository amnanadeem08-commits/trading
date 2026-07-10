"""Audit storage contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from threading import RLock

from models.events import AuditRecord


class AuditStore(ABC):
    """Append-only audit storage contract."""

    @abstractmethod
    def write(self, record: AuditRecord) -> None:
        """Append an audit record. No updates or deletes."""

    @abstractmethod
    def read(
        self,
        *,
        market_id: str | None = None,
        symbol_id: str | None = None,
        event_id: str | None = None,
    ) -> tuple[AuditRecord, ...]:
        """Read audit records with optional filters."""

    @abstractmethod
    def count(self) -> int:
        """Return total audit record count."""


class InMemoryAuditStore(AuditStore):
    """In-memory append-only audit store for Phase 0 scaffold."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: list[AuditRecord] = []

    def write(self, record: AuditRecord) -> None:
        with self._lock:
            self._records.append(record)

    def read(
        self,
        *,
        market_id: str | None = None,
        symbol_id: str | None = None,
        event_id: str | None = None,
    ) -> tuple[AuditRecord, ...]:
        with self._lock:
            records = list(self._records)
        if market_id is not None:
            records = [record for record in records if record.market_id == market_id]
        if symbol_id is not None:
            records = [record for record in records if record.symbol_id == symbol_id]
        if event_id is not None:
            records = [record for record in records if record.event_id == event_id]
        return tuple(records)

    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def clear(self) -> None:
        """Clear audit records. Intended for tests only."""
        with self._lock:
            self._records.clear()
