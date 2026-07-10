"""LLM provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.llm.llm_request import LLMRequest
from ai.llm.llm_response import LLMResponse


class LLMProvider(ABC):
    """Provider-independent LLM invocation contract."""

    @abstractmethod
    def provider_id(self) -> str:
        """Return the provider identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the provider display name."""

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Complete an LLM request and return a response."""


class StubLLMProvider(LLMProvider):
    """Stub LLM provider for platform scaffolding."""

    def __init__(self, *, provider_id: str = "stub", name: str = "Stub Provider") -> None:
        self._provider_id = provider_id
        self._name = name

    def provider_id(self) -> str:
        return self._provider_id

    def name(self) -> str:
        return self._name

    def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            request_id=request.request_id,
            provider_id=self._provider_id,
            content=f"[stub-response] {request.prompt[:80]}",
            model_name=request.model_name,
            token_count=len(request.prompt.split()),
            metadata={"provider": self._name},
        )
