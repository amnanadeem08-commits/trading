"""Unit tests for AI agent contracts."""

from __future__ import annotations

import inspect

import pytest

from ai import TERMINAL_AGENT_STATES, Agent, AgentState
from tests.ai_helpers import SampleAgent, make_agent_metadata


@pytest.mark.unit
def test_agent_contract_methods() -> None:
    methods = {name for name, _ in inspect.getmembers(Agent, predicate=inspect.isfunction)}
    assert "agent_id" in methods
    assert "execute" in methods


@pytest.mark.unit
def test_sample_agent_satisfies_contract() -> None:
    agent = SampleAgent()
    assert agent.agent_id() == "sample-agent"
    assert agent.capabilities() == ("reasoning",)


@pytest.mark.unit
def test_agent_metadata_fields() -> None:
    metadata = make_agent_metadata()
    assert metadata.agent_id == "sample-agent"
    assert metadata.capabilities == ("reasoning",)


@pytest.mark.unit
def test_terminal_agent_states() -> None:
    assert AgentState.COMPLETED in TERMINAL_AGENT_STATES
    assert AgentState.RUNNING not in TERMINAL_AGENT_STATES
