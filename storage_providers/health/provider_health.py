"""Provider health checker."""

from __future__ import annotations

from storage_providers.exceptions import ProviderHealthError, ProviderNotFoundError
from storage_providers.health.health_result import HealthStatus, ProviderHealthResult
from storage_providers.registry.provider_record import ProviderState
from storage_providers.registry.provider_registry import ProviderRegistry


class ProviderHealthChecker:
    """Performs metadata-only health checks for registered providers."""

    def __init__(self, *, registry: ProviderRegistry) -> None:
        self._registry = registry

    def check(self, provider_id: str) -> ProviderHealthResult:
        try:
            record = self._registry.lookup(provider_id)
        except ProviderNotFoundError as error:
            raise ProviderHealthError(str(error)) from error

        if record.state == ProviderState.FAILED:
            return ProviderHealthResult(
                provider_id=provider_id,
                status=HealthStatus.UNHEALTHY,
                message="provider in failed state",
            )
        if record.state == ProviderState.SHUTDOWN:
            return ProviderHealthResult(
                provider_id=provider_id,
                status=HealthStatus.DEGRADED,
                message="provider has been shut down",
            )
        return ProviderHealthResult(
            provider_id=provider_id,
            status=HealthStatus.HEALTHY,
            message=record.state.value,
            details={
                "provider_id": provider_id,
                "state": record.state.value,
                "provider_type": record.manifest.provider_type.value,
            },
        )
