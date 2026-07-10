"""Unit tests for AI memory framework."""

from __future__ import annotations

import pytest

from ai import ConversationMemory, InMemoryStore, MemoryEntry


@pytest.mark.unit
def test_in_memory_store_operations() -> None:
    store = InMemoryStore()
    entry = MemoryEntry(
        entry_id="entry-1",
        session_id="session-1",
        role="user",
        content="hello",
    )
    store.store(entry)
    assert len(store.retrieve("session-1")) == 1
    store.clear("session-1")
    assert store.retrieve("session-1") == ()


@pytest.mark.unit
def test_conversation_memory_interactions() -> None:
    memory = ConversationMemory()
    memory.add_interaction(role="user", content="input")
    memory.add_interaction(role="assistant", content="output")
    assert memory.interaction_count() == 2
    memory.clear()
    assert memory.interaction_count() == 0
