"""LLM provider registry."""

from __future__ import annotations

from threading import RLock

from ai.exceptions import LLMProviderError, LLMProviderNotFoundError
from ai.llm.llm_provider import LLMProvider

_default_llm_registry: LLMRegistry | None = None
_registry_lock = RLock()


class LLMRegistry:
    """Thread-safe registry for LLM providers."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._providers: dict[str, LLMProvider] = {}

    def register(self, provider: LLMProvider) -> None:
        provider_id = provider.provider_id()
        if not provider_id.strip():
            msg = "Provider id must not be empty"
            raise LLMProviderError(msg)
        with self._lock:
            if provider_id in self._providers:
                msg = f"LLM provider already registered: {provider_id}"
                raise LLMProviderError(msg)
            self._providers[provider_id] = provider

    def resolve(self, provider_id: str) -> LLMProvider:
        with self._lock:
            provider = self._providers.get(provider_id)
        if provider is None:
            raise LLMProviderNotFoundError(provider_id)
        return provider

    def exists(self, provider_id: str) -> bool:
        with self._lock:
            return provider_id in self._providers

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._providers.keys()))


def get_llm_registry() -> LLMRegistry:
    """Return the process-wide default LLM registry."""
    global _default_llm_registry
    with _registry_lock:
        if _default_llm_registry is None:
            _default_llm_registry = LLMRegistry()
        return _default_llm_registry


def reset_llm_registry() -> None:
    """Reset the default LLM registry. Intended for tests."""
    global _default_llm_registry
    with _registry_lock:
        _default_llm_registry = None
