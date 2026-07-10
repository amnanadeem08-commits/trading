"""Audit record reader."""

from __future__ import annotations

from audit._store import AuditStore, InMemoryAuditStore
from models.events import AuditRecord


class AuditReader:
    """Reads audit records from an append-only store."""

    def __init__(self, store: AuditStore | None = None) -> None:
        self._store = store or InMemoryAuditStore()

    def read(
        self,
        *,
        market_id: str | None = None,
        symbol_id: str | None = None,
        event_id: str | None = None,
    ) -> tuple[AuditRecord, ...]:
        return self._store.read(
            market_id=market_id,
            symbol_id=symbol_id,
            event_id=event_id,
        )

    def count(self) -> int:
        return self._store.count()
