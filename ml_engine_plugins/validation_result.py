"""Plugin validation result."""

from __future__ import annotations

from models.common import PlatformModel


class PluginValidationResult(PlatformModel):
    """Validation result for plugin operations."""

    valid: bool
    errors: tuple[str, ...] = ()
    plugin_id: str | None = None

    @classmethod
    def success(cls, *, plugin_id: str | None = None) -> PluginValidationResult:
        return cls(valid=True, plugin_id=plugin_id)

    @classmethod
    def failure(cls, *errors: str, plugin_id: str | None = None) -> PluginValidationResult:
        return cls(valid=False, errors=errors, plugin_id=plugin_id)
