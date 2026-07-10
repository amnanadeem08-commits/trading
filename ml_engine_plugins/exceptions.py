"""ML engine plugin exceptions."""


class MLEnginePluginError(Exception):
    """Base exception for ML engine plugin errors."""


class PluginNotFoundError(MLEnginePluginError):
    """Raised when a plugin is not registered."""


class PluginLoadError(MLEnginePluginError):
    """Raised when plugin loading fails."""


class PluginValidationError(MLEnginePluginError):
    """Raised when plugin validation fails."""


class PluginDiscoveryError(MLEnginePluginError):
    """Raised when plugin discovery fails."""


class PluginHealthError(MLEnginePluginError):
    """Raised when plugin health checks fail."""
