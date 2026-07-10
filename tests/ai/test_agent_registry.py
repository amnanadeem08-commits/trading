"""Unit tests for AI agent registry."""

from __future__ import annotations

import pytest

from ai import (
    AgentRegistrationError,
    AgentRegistry,
    AgentState,
    get_agent_registry,
    reset_agent_registry,
)
from tests.ai_helpers import SampleAgent, make_agent_metadata


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_agent_registry()
    yield
    reset_agent_registry()


@pytest.mark.unit
def test_agent_registry_register_and_resolve() -> None:
    registry = AgentRegistry()
    metadata = make_agent_metadata()
    registry.register(metadata)
    resolved = registry.resolve("sample-agent")
    assert resolved.name == "Sample Agent"
    assert registry.get_state("sample-agent") == AgentState.CREATED


@pytest.mark.unit
def test_agent_registry_register_type() -> None:
    registry = AgentRegistry()
    registry.register_type(SampleAgent)
    agent_type = registry.resolve_type("sample-agent")
    assert agent_type is SampleAgent


@pytest.mark.unit
def test_agent_registry_duplicate_raises() -> None:
    registry = AgentRegistry()
    registry.register(make_agent_metadata())
    with pytest.raises(AgentRegistrationError):
        registry.register(make_agent_metadata())


@pytest.mark.unit
def test_agent_registry_state_transitions() -> None:
    registry = AgentRegistry()
    registry.register(make_agent_metadata())
    registry.set_state("sample-agent", AgentState.RUNNING)
    assert registry.get_state("sample-agent") == AgentState.RUNNING


@pytest.mark.unit
def test_get_agent_registry_singleton() -> None:
    first = get_agent_registry()
    second = get_agent_registry()
    assert first is second
