"""Strategy version registry."""

from __future__ import annotations

from versioning._base import VersionRegistry

_strategy_registry: VersionRegistry | None = None


def get_strategy_registry() -> VersionRegistry:
    global _strategy_registry
    if _strategy_registry is None:
        _strategy_registry = VersionRegistry("strategy")
    return _strategy_registry


def reset_strategy_registry() -> None:
    global _strategy_registry
    _strategy_registry = None
