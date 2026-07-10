"""Connector version registry."""

from __future__ import annotations

from versioning._base import VersionRegistry

_connector_registry: VersionRegistry | None = None


def get_connector_version_registry() -> VersionRegistry:
    global _connector_registry
    if _connector_registry is None:
        _connector_registry = VersionRegistry("connector")
    return _connector_registry


def reset_connector_version_registry() -> None:
    global _connector_registry
    _connector_registry = None
