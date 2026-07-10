"""Prompt registry."""

from __future__ import annotations

from threading import RLock

from ai.exceptions import PromptNotFoundError, PromptRegistrationError
from ai.prompts.prompt import Prompt
from ai.prompts.prompt_template import PromptTemplate

_default_prompt_registry: PromptRegistry | None = None
_registry_lock = RLock()


class PromptRegistry:
    """Thread-safe registry for prompts and templates."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._prompts: dict[str, Prompt] = {}
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, prompt: Prompt) -> None:
        prompt_id = prompt.prompt_id
        if not prompt_id.strip():
            msg = "Prompt id must not be empty"
            raise PromptRegistrationError(msg)
        with self._lock:
            if prompt_id in self._prompts:
                msg = f"Prompt already registered: {prompt_id}"
                raise PromptRegistrationError(msg)
            self._prompts[prompt_id] = prompt

    def register_template(self, template: PromptTemplate) -> None:
        template_id = template.template_id
        with self._lock:
            if template_id in self._templates:
                msg = f"Prompt template already registered: {template_id}"
                raise PromptRegistrationError(msg)
            self._templates[template_id] = template

    def resolve(self, prompt_id: str) -> Prompt:
        with self._lock:
            prompt = self._prompts.get(prompt_id)
        if prompt is None:
            raise PromptNotFoundError(prompt_id)
        return prompt

    def resolve_template(self, template_id: str) -> PromptTemplate:
        with self._lock:
            template = self._templates.get(template_id)
        if template is None:
            raise PromptNotFoundError(template_id)
        return template

    def exists(self, prompt_id: str) -> bool:
        with self._lock:
            return prompt_id in self._prompts

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._prompts.keys()))

    def list_templates(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._templates.keys()))


def get_prompt_registry() -> PromptRegistry:
    """Return the process-wide default prompt registry."""
    global _default_prompt_registry
    with _registry_lock:
        if _default_prompt_registry is None:
            _default_prompt_registry = PromptRegistry()
        return _default_prompt_registry


def reset_prompt_registry() -> None:
    """Reset the default prompt registry. Intended for tests."""
    global _default_prompt_registry
    with _registry_lock:
        _default_prompt_registry = None
