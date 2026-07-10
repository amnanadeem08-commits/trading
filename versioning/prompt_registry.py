"""Prompt version registry."""

from __future__ import annotations

from versioning._base import VersionRegistry

_prompt_registry: VersionRegistry | None = None


def get_prompt_registry() -> VersionRegistry:
    global _prompt_registry
    if _prompt_registry is None:
        _prompt_registry = VersionRegistry("prompt")
    return _prompt_registry


def reset_prompt_registry() -> None:
    global _prompt_registry
    _prompt_registry = None
