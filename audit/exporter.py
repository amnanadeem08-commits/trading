"""Audit record export."""

from __future__ import annotations

import json

from audit._store import AuditStore, InMemoryAuditStore
from models.events import AuditRecord


class AuditExporter:
    """Exports audit records for compliance and investigation."""

    def __init__(self, store: AuditStore | None = None) -> None:
        self._store = store or InMemoryAuditStore()

    def export_json(
        self,
        *,
        market_id: str | None = None,
        symbol_id: str | None = None,
        event_id: str | None = None,
    ) -> str:
        records = self._store.read(
            market_id=market_id,
            symbol_id=symbol_id,
            event_id=event_id,
        )
        payload = [record.model_dump(mode="json") for record in records]
        return json.dumps(payload, indent=2, default=str)

    def export_records(
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
