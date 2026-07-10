"""Append-only audit logger."""

from __future__ import annotations

from audit._store import AuditStore, InMemoryAuditStore
from models.events import AuditRecord


class AuditLogger:
    """Writes immutable audit records."""

    def __init__(self, store: AuditStore | None = None) -> None:
        self._store = store or InMemoryAuditStore()

    @property
    def store(self) -> AuditStore:
        return self._store

    def write(self, record: AuditRecord) -> AuditRecord:
        """Append an audit record and return it."""
        self._store.write(record)
        return record
