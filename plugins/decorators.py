"""Plugin registration decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from plugins.plugin import BasePlugin

PluginType = TypeVar("PluginType", bound=BasePlugin)

_PLUGIN_METADATA_KEY = "_platform_plugin_metadata"


def plugin(
    *,
    plugin_id: str | None = None,
    auto_register: bool = True,
) -> Callable[[PluginType], PluginType]:
    """Attach discovery metadata to a plugin implementation."""

    def decorator(defn: PluginType) -> PluginType:
        setattr(
            defn,
            _PLUGIN_METADATA_KEY,
            {
                "plugin_id": plugin_id,
                "auto_register": auto_register,
            },
        )
        return defn

    return decorator


def plugin_metadata(defn: type[BasePlugin] | BasePlugin) -> dict[str, str | bool | None]:
    """Return discovery metadata attached to a plugin implementation."""
    metadata = getattr(defn, _PLUGIN_METADATA_KEY, None)
    if metadata is None:
        return {"plugin_id": None, "auto_register": False}
    return dict(metadata)
