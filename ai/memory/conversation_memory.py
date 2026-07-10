"""Conversation memory interface."""

from __future__ import annotations

from uuid import uuid4

from ai.memory.memory_store import InMemoryStore, MemoryEntry, MemoryStore
from models.common import utc_now


class ConversationMemory:
    """Manages conversation interactions in a memory store."""

    def __init__(self, *, store: MemoryStore | None = None, session_id: str | None = None) -> None:
        self._store = store or InMemoryStore()
        self._session_id = session_id or str(uuid4())

    @property
    def session_id(self) -> str:
        return self._session_id

    def add_interaction(
        self, *, role: str, content: str, metadata: dict[str, str] | None = None
    ) -> MemoryEntry:
        entry = MemoryEntry(
            entry_id=str(uuid4()),
            session_id=self._session_id,
            role=role,
            content=content,
            metadata=metadata or {},
            created_at=utc_now(),
        )
        return self._store.store(entry)

    def get_context(self) -> tuple[MemoryEntry, ...]:
        return self._store.retrieve(self._session_id)

    def clear(self) -> None:
        self._store.clear(self._session_id)

    def interaction_count(self) -> int:
        return len(self.get_context())
