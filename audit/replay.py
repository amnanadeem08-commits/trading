"""Audit replay scaffold."""

from __future__ import annotations

from collections.abc import Callable

from audit._store import AuditStore, InMemoryAuditStore
from models.events import AuditRecord


class AuditReplayer:
    """Replays audit records for investigation without mutation."""

    def __init__(self, store: AuditStore | None = None) -> None:
        self._store = store or InMemoryAuditStore()

    def replay(
        self,
        handler: Callable[[AuditRecord], None],
        *,
        market_id: str | None = None,
        symbol_id: str | None = None,
    ) -> int:
        records = self._store.read(market_id=market_id, symbol_id=symbol_id)
        for record in records:
            handler(record)
        return len(records)
