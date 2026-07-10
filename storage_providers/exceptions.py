"""Storage provider exceptions."""


class StorageProviderError(Exception):
    """Base exception for storage provider errors."""


class ProviderNotFoundError(StorageProviderError):
    """Raised when a storage provider is not registered."""


class ProviderValidationError(StorageProviderError):
    """Raised when storage provider validation fails."""


class ProviderResolutionError(StorageProviderError):
    """Raised when storage provider resolution fails."""


class ProviderHealthError(StorageProviderError):
    """Raised when storage provider health checks fail."""


class ProviderPathError(StorageProviderError):
    """Raised when a storage URI resolves to an invalid sandbox path."""


class ProviderFilesystemError(StorageProviderError):
    """Raised when filesystem metadata operations fail."""
