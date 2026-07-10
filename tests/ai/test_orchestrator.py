"""Unit tests for AI orchestrator."""

from __future__ import annotations

import pytest

from ai import AgentRegistry, AIOrchestrator, OrchestrationError, Prompt, PromptRegistry
from core import CoreRuntime
from pipeline import build_pipeline_context
from services import reset_application_context
from tests.ai_helpers import FailingAgent, SampleAgent, make_agent_metadata


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_application_context()
    yield
    reset_application_context()


@pytest.mark.unit
def test_orchestrator_create_and_execute_task() -> None:
    agents = AgentRegistry()
    prompts = PromptRegistry()
    agents.register(make_agent_metadata())
    agents.register_type(SampleAgent)
    prompts.register(
        Prompt(prompt_id="task-prompt", name="Task", version="1.0.0", content="Run task"),
    )
    orchestrator = AIOrchestrator(agent_registry=agents, prompt_registry=prompts)
    runtime = CoreRuntime(context=build_pipeline_context())
    core_context = runtime.initialize()
    task = orchestrator.create_task(
        agent_id="sample-agent",
        core_context=core_context,
        prompt_id="task-prompt",
        input_data={"key": "value"},
    )
    result = orchestrator.execute(task, SampleAgent())
    assert result.confidence >= 0.9
    assert agents.get_state("sample-agent").value == "completed"


@pytest.mark.unit
def test_orchestrator_execution_failure() -> None:
    agents = AgentRegistry()
    agents.register(make_agent_metadata(agent_id="failing-agent"))
    agents.register_type(FailingAgent)
    orchestrator = AIOrchestrator(agent_registry=agents)
    task = orchestrator.create_task(agent_id="failing-agent")
    with pytest.raises(OrchestrationError):
        orchestrator.execute(task, FailingAgent())
