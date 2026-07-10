"""Unit tests for prompt registry."""

from __future__ import annotations

import pytest

from ai import Prompt, PromptNotFoundError, PromptRegistrationError, PromptRegistry, PromptTemplate


@pytest.mark.unit
def test_prompt_registry_register_and_resolve() -> None:
    registry = PromptRegistry()
    prompt = Prompt(
        prompt_id="greeting",
        name="Greeting",
        version="1.0.0",
        content="Hello",
    )
    registry.register(prompt)
    assert registry.resolve("greeting").content == "Hello"


@pytest.mark.unit
def test_prompt_registry_template() -> None:
    registry = PromptRegistry()
    template = PromptTemplate.from_template(
        template_id="tpl-1",
        name="Template",
        version="1.0.0",
        template="Input: {value}",
    )
    registry.register_template(template)
    assert registry.list_templates() == ("tpl-1",)


@pytest.mark.unit
def test_prompt_registry_duplicate_raises() -> None:
    registry = PromptRegistry()
    prompt = Prompt(prompt_id="dup", name="Dup", version="1.0.0", content="x")
    registry.register(prompt)
    with pytest.raises(PromptRegistrationError):
        registry.register(prompt)


@pytest.mark.unit
def test_prompt_registry_missing_raises() -> None:
    registry = PromptRegistry()
    with pytest.raises(PromptNotFoundError):
        registry.resolve("missing")
