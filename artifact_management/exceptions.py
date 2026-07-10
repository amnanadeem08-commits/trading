"""Artifact management exceptions."""


class ArtifactManagementError(Exception):
    """Base exception for artifact management errors."""


class ArtifactNotFoundError(ArtifactManagementError):
    """Raised when an artifact is not registered."""


class ArtifactValidationError(ArtifactManagementError):
    """Raised when artifact validation fails."""


class ArtifactResolutionError(ArtifactManagementError):
    """Raised when artifact resolution fails."""


class ArtifactCacheError(ArtifactManagementError):
    """Raised when artifact cache operations fail."""


class ArtifactHealthError(ArtifactManagementError):
    """Raised when artifact health checks fail."""
