"""Adapter health checker."""

from __future__ import annotations

from framework_adapters.exceptions import AdapterHealthError, AdapterNotFoundError
from framework_adapters.health.health_result import FrameworkAdapterHealthResult, HealthStatus
from framework_adapters.registry.adapter_record import AdapterState
from framework_adapters.registry.adapter_registry import AdapterRegistry


class FrameworkAdapterHealthChecker:
    """Performs metadata-only health checks for registered adapters."""

    def __init__(
        self,
        *,
        registry: AdapterRegistry,
    ) -> None:
        self._registry = registry

    def check(self, adapter_id: str) -> FrameworkAdapterHealthResult:
        try:
            record = self._registry.lookup(adapter_id)
            adapter = self._registry.get_adapter(adapter_id)
        except AdapterNotFoundError as error:
            raise AdapterHealthError(str(error)) from error

        if record.state == AdapterState.FAILED:
            result = FrameworkAdapterHealthResult(
                adapter_id=adapter_id,
                status=HealthStatus.UNHEALTHY,
                message="adapter in failed state",
            )
        else:
            environment = adapter.validate_environment()
            status_value = str(environment.get("status", "healthy"))
            status = HealthStatus.HEALTHY if status_value == "healthy" else HealthStatus.DEGRADED
            result = FrameworkAdapterHealthResult(
                adapter_id=adapter_id,
                status=status,
                message=status_value,
                details=environment,
            )
            self._registry.update_state(adapter_id, AdapterState.HEALTHY)

        return result
