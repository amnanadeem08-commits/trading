"""Memory store interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class MemoryEntry(PlatformModel):
    """Stored memory entry."""

    entry_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    content: str = Field(min_length=1)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: UTCDateTime = Field(default_factory=utc_now)


class MemoryStore(ABC):
    """Generic memory storage contract."""

    @abstractmethod
    def store(self, entry: MemoryEntry) -> MemoryEntry:
        """Store a memory entry."""

    @abstractmethod
    def retrieve(self, session_id: str) -> tuple[MemoryEntry, ...]:
        """Retrieve memory entries for a session."""

    @abstractmethod
    def clear(self, session_id: str) -> None:
        """Clear memory entries for a session."""


class InMemoryStore(MemoryStore):
    """In-memory memory store for platform scaffolding."""

    def __init__(self) -> None:
        self._entries: dict[str, list[MemoryEntry]] = {}

    def store(self, entry: MemoryEntry) -> MemoryEntry:
        self._entries.setdefault(entry.session_id, []).append(entry)
        return entry

    def retrieve(self, session_id: str) -> tuple[MemoryEntry, ...]:
        return tuple(self._entries.get(session_id, ()))

    def clear(self, session_id: str) -> None:
        self._entries.pop(session_id, None)

    def count(self, session_id: str) -> int:
        return len(self._entries.get(session_id, ()))
