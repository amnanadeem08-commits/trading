"""Plugin statistics contracts."""

from __future__ import annotations

from models.common import PlatformModel


class PluginStatistics(PlatformModel):
    """Aggregate plugin framework statistics."""

    total_plugins: int = 0
    discovered_plugins: int = 0
    registered_plugins: int = 0
    loaded_plugins: int = 0
    validated_plugins: int = 0
    healthy_plugins: int = 0
    failed_plugins: int = 0
    unloaded_plugins: int = 0
