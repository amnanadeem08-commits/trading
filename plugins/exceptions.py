"""Plugin framework exceptions."""

from __future__ import annotations

from models.common import PlatformError


class PluginError(PlatformError):
    """Base exception for plugin framework errors."""

    def __init__(self, message: str, *, code: str = "plugin_error") -> None:
        super().__init__(message, code=code)


class PluginNotFoundError(PluginError):
    """Raised when a plugin cannot be resolved."""

    def __init__(self, plugin_id: str) -> None:
        super().__init__(f"Plugin not found: {plugin_id}", code="plugin_not_found")
        self.plugin_id = plugin_id


class PluginRegistrationError(PluginError):
    """Raised when plugin registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="plugin_registration_error")


class PluginValidationError(PluginError):
    """Raised when plugin validation fails."""

    def __init__(self, message: str, *, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message, code="plugin_validation_error")
        self.errors = errors


class PluginLoadError(PluginError):
    """Raised when plugin loading fails."""

    def __init__(self, message: str, *, plugin_id: str | None = None) -> None:
        super().__init__(message, code="plugin_load_error")
        self.plugin_id = plugin_id


class PluginCompatibilityError(PluginError):
    """Raised when plugin version compatibility checks fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="plugin_compatibility_error")


class CircularPluginDependencyError(PluginValidationError):
    """Raised when plugin dependencies form a cycle."""

    def __init__(self, cycle: tuple[str, ...]) -> None:
        cycle_path = " -> ".join(cycle)
        super().__init__(f"Circular plugin dependency: {cycle_path}", errors=(cycle_path,))
        self.cycle = cycle


class PluginStateError(PluginError):
    """Raised when an invalid plugin state transition is attempted."""

    def __init__(self, plugin_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} plugin '{plugin_id}' in state '{current_state}'",
            code="plugin_state_error",
        )
        self.plugin_id = plugin_id
        self.current_state = current_state
        self.operation = operation


class PermissionConflictError(PluginValidationError):
    """Raised when plugin permissions conflict."""

    def __init__(self, message: str, *, conflicts: tuple[str, ...] = ()) -> None:
        super().__init__(message, errors=conflicts)
        self.conflicts = conflicts
