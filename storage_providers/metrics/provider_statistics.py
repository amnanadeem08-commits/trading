"""Provider statistics contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class ProviderStatistics(PlatformModel):
    """Aggregate statistics for storage provider operations."""

    total_providers: int = 0
    registered_providers: int = 0
    validated_providers: int = 0
    resolved_providers: int = 0
    healthy_providers: int = 0
    failed_providers: int = 0
    shutdown_providers: int = 0
    provider_registrations: int = 0
    provider_resolutions: int = 0
    provider_validations: int = 0
    provider_failures: int = 0
    provider_usage: dict[str, int] = Field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    validation_failures: int = 0
    resolution_failures: int = 0
    filesystem_lookups: int = 0
    checksum_operations: int = 0
    missing_files: int = 0
    invalid_paths: int = 0
