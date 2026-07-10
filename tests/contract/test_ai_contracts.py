"""Contract tests for AI layer."""

from __future__ import annotations

import inspect

import pytest

from ai import (
    Agent,
    AgentContext,
    AITask,
    LLMRequest,
    LLMResponse,
    PromptTemplate,
    ReasoningResult,
)
from tests.ai_helpers import SampleAgent


@pytest.mark.contract
def test_agent_contract() -> None:
    methods = {name for name, _ in inspect.getmembers(Agent, predicate=inspect.isfunction)}
    assert "execute" in methods
    assert "initialize" in methods


@pytest.mark.contract
def test_sample_agent_contract_compliance() -> None:
    agent = SampleAgent()
    context = AgentContext(agent_id=agent.agent_id(), task_id="task-1")
    result = agent.execute(context)
    assert isinstance(result, ReasoningResult)
    assert result.agent_id == "sample-agent"


@pytest.mark.contract
def test_ai_task_fields() -> None:
    task = AITask(task_id="task-1", agent_id="sample-agent")
    assert task.state.value == "created"


@pytest.mark.contract
def test_llm_request_response_fields() -> None:
    request = LLMRequest(request_id="req-1", provider_id="stub", prompt="test")
    response = LLMResponse(request_id="req-1", provider_id="stub", content="ok")
    assert request.prompt == "test"
    assert response.content == "ok"


@pytest.mark.contract
def test_prompt_template_contract() -> None:
    template = PromptTemplate.from_template(
        template_id="tpl",
        name="Template",
        version="1.0.0",
        template="Value: {value}",
    )
    assert template.render({"value": "42"}) == "Value: 42"
