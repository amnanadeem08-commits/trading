"""Schema version registry."""

from __future__ import annotations

from versioning._base import VersionRegistry

_schema_registry: VersionRegistry | None = None


def get_schema_registry() -> VersionRegistry:
    global _schema_registry
    if _schema_registry is None:
        _schema_registry = VersionRegistry("schema")
    return _schema_registry


def reset_schema_registry() -> None:
    global _schema_registry
    _schema_registry = None
