"""Unit tests for prompt framework."""

from __future__ import annotations

import pytest

from ai import Prompt, PromptTemplate


@pytest.mark.unit
def test_prompt_fields() -> None:
    prompt = Prompt(
        prompt_id="greeting",
        name="Greeting",
        version="1.0.0",
        content="Hello, {name}!",
    )
    assert prompt.prompt_id == "greeting"


@pytest.mark.unit
def test_prompt_template_render() -> None:
    template = PromptTemplate.from_template(
        template_id="greeting-template",
        name="Greeting Template",
        version="1.0.0",
        template="Process input: {input_text} with mode {mode}",
    )
    rendered = template.render({"input_text": "sample", "mode": "test"})
    assert "sample" in rendered
    assert template.variables == ("input_text", "mode")


@pytest.mark.unit
def test_prompt_template_missing_variable_raises() -> None:
    template = PromptTemplate.from_template(
        template_id="incomplete",
        name="Incomplete",
        version="1.0.0",
        template="Value: {value}",
    )
    with pytest.raises(KeyError):
        template.render({})
