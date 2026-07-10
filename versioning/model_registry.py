"""ML model version registry."""

from __future__ import annotations

from versioning._base import VersionRegistry

_model_registry: VersionRegistry | None = None


def get_model_registry() -> VersionRegistry:
    global _model_registry
    if _model_registry is None:
        _model_registry = VersionRegistry("model")
    return _model_registry


def reset_model_registry() -> None:
    global _model_registry
    _model_registry = None
