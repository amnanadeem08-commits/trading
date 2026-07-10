"""Unit tests for reasoning framework."""

from __future__ import annotations

import pytest

from ai import PassthroughReasoningEngine, ReasoningContext
from ai.agents.agent_context import AgentContext
from tests.ai_helpers import SampleAgent


@pytest.mark.unit
def test_passthrough_reasoning_engine() -> None:
    engine = PassthroughReasoningEngine()
    agent = SampleAgent()
    context = AgentContext(agent_id=agent.agent_id(), task_id="task-1")
    reasoning_context = ReasoningContext(
        reasoning_id="reason-1",
        agent_context=context,
        input_data={"value": 42},
    )
    result = engine.reason(reasoning_context)
    assert result.output["value"] == 42
    assert result.metadata["engine"] == "passthrough"
