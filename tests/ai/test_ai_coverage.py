"""Additional AI layer coverage tests."""

from __future__ import annotations

import pytest

from ai import (
    AgentNotFoundError,
    AgentRegistrationError,
    AgentStateError,
    AIError,
    LLMProviderNotFoundError,
    LLMRegistry,
    PromptNotFoundError,
    PromptRegistry,
    get_llm_registry,
    get_prompt_registry,
    reset_agent_registry,
    reset_llm_registry,
    reset_prompt_registry,
)
from ai.agents.agent_registry import AgentRegistry
from ai.exceptions import OrchestrationError
from tests.ai_helpers import SampleAgent, make_agent_metadata


@pytest.fixture(autouse=True)
def _reset_registries() -> None:
    reset_agent_registry()
    reset_prompt_registry()
    reset_llm_registry()
    yield
    reset_agent_registry()
    reset_prompt_registry()
    reset_llm_registry()


@pytest.mark.unit
def test_exception_codes() -> None:
    assert AIError("x").code == "ai_error"
    assert AgentNotFoundError("a").code == "agent_not_found"
    assert AgentRegistrationError("x").code == "agent_registration_error"
    assert AgentStateError("a", "running", "stop").code == "agent_state_error"
    assert PromptNotFoundError("p").code == "prompt_not_found"
    assert LLMProviderNotFoundError("l").code == "llm_provider_not_found"
    assert OrchestrationError("x").code == "orchestration_error"


@pytest.mark.unit
def test_agent_registry_unregister_and_list_types() -> None:
    registry = AgentRegistry()
    registry.register(make_agent_metadata())
    registry.register_type(SampleAgent)
    registry.unregister("sample-agent")
    with pytest.raises(AgentNotFoundError):
        registry.resolve("sample-agent")


@pytest.mark.unit
def test_prompt_registry_singleton_and_exists() -> None:
    registry = get_prompt_registry()
    from ai import Prompt

    registry.register(Prompt(prompt_id="singleton", name="S", version="1.0.0", content="x"))
    assert get_prompt_registry().exists("singleton") is True
    assert "singleton" in registry.list()


@pytest.mark.unit
def test_llm_registry_singleton_and_list() -> None:
    from ai import StubLLMProvider

    registry = get_llm_registry()
    registry.register(StubLLMProvider(provider_id="custom"))
    assert registry.exists("custom") is True
    assert "custom" in registry.list()


@pytest.mark.unit
def test_llm_registry_resolve_missing_raises() -> None:
    registry = LLMRegistry()
    with pytest.raises(LLMProviderNotFoundError):
        registry.resolve("missing")


@pytest.mark.unit
def test_prompt_registry_resolve_template_missing_raises() -> None:
    registry = PromptRegistry()
    with pytest.raises(PromptNotFoundError):
        registry.resolve_template("missing")
