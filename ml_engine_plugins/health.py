"""Plugin health checker."""

from __future__ import annotations

from ml_engine_plugins.exceptions import PluginHealthError, PluginNotFoundError
from ml_engine_plugins.health_result import PluginHealthResult, PluginHealthStatus
from ml_engine_plugins.plugin_lifecycle import PluginLifecycleManager
from ml_engine_plugins.plugin_registry import PluginRegistry
from ml_engine_plugins.plugin_state import PluginState


class PluginHealthChecker:
    """Performs metadata-only health checks for registered plugins."""

    def __init__(
        self,
        *,
        registry: PluginRegistry,
        lifecycle: PluginLifecycleManager | None = None,
    ) -> None:
        self._registry = registry
        self._lifecycle = lifecycle

    def check(self, plugin_id: str) -> PluginHealthResult:
        try:
            record = self._registry.lookup(plugin_id)
            plugin = self._registry.get_plugin(plugin_id)
        except PluginNotFoundError as error:
            raise PluginHealthError(str(error)) from error

        if record.state == PluginState.FAILED:
            result = PluginHealthResult(
                plugin_id=plugin_id,
                status=PluginHealthStatus.UNHEALTHY,
                message="plugin in failed state",
            )
        else:
            health = plugin.create_executor().health()
            status_value = str(health.get("status", "healthy"))
            status = (
                PluginHealthStatus.HEALTHY
                if status_value == "healthy"
                else PluginHealthStatus.DEGRADED
            )
            result = PluginHealthResult(
                plugin_id=plugin_id,
                status=status,
                message=status_value,
                details=health,
            )
            self._registry.update_state(plugin_id, PluginState.HEALTHY)

        if self._lifecycle is not None:
            self._lifecycle.emit_plugin_health_checked(
                plugin_id=plugin_id,
                status=result.status.value,
                correlation_id=plugin_id,
                trace_id=plugin_id,
            )
        return result
