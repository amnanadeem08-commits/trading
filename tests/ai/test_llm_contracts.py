"""Unit tests for LLM contracts."""

from __future__ import annotations

import pytest

from ai import LLMRegistry, LLMRequest, StubLLMProvider


@pytest.mark.unit
def test_stub_llm_provider_complete() -> None:
    provider = StubLLMProvider()
    request = LLMRequest(
        request_id="req-1",
        provider_id="stub",
        prompt="Analyze the input data",
    )
    response = provider.complete(request)
    assert response.provider_id == "stub"
    assert "stub-response" in response.content


@pytest.mark.unit
def test_llm_registry_register_and_resolve() -> None:
    registry = LLMRegistry()
    provider = StubLLMProvider(provider_id="custom")
    registry.register(provider)
    resolved = registry.resolve("custom")
    assert resolved.name() == "Stub Provider"


@pytest.mark.unit
def test_llm_request_fields() -> None:
    request = LLMRequest(
        request_id="req-1",
        provider_id="stub",
        prompt="test prompt",
        model_name="default",
    )
    assert request.model_name == "default"
