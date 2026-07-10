"""Health component registry."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock

from health.models import ComponentHealth, DependencyStatus, HealthState
from models.common import ContractViolationError

type HealthCheckFn = Callable[[], tuple[HealthState, str]]


class HealthComponent:
    """Registered health-checkable component."""

    def __init__(
        self,
        name: str,
        check_fn: HealthCheckFn,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        self.name = name
        self.check_fn = check_fn
        self.dependencies = dependencies


class HealthRegistry:
    """Registry for health-checkable components."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._components: dict[str, HealthComponent] = {}
        self._dependencies: dict[str, DependencyStatus] = {}

    def register(
        self,
        name: str,
        check_fn: HealthCheckFn,
        *,
        dependencies: tuple[str, ...] = (),
    ) -> None:
        """Register a component health check."""
        with self._lock:
            self._components[name] = HealthComponent(name, check_fn, dependencies)

    def unregister(self, name: str) -> None:
        """Remove a registered component."""
        with self._lock:
            if name not in self._components:
                msg = f"Health component not registered: {name}"
                raise ContractViolationError(msg)
            del self._components[name]

    def register_dependency(self, status: DependencyStatus) -> None:
        """Register or update a dependency status."""
        with self._lock:
            self._dependencies[status.name] = status

    def dependency_status(self, name: str) -> DependencyStatus | None:
        with self._lock:
            return self._dependencies.get(name)

    def list_components(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._components.keys()))

    def check_all(self) -> tuple[ComponentHealth, ...]:
        """Run all registered component health checks."""
        results: list[ComponentHealth] = []
        with self._lock:
            components = list(self._components.values())
            dependencies = dict(self._dependencies)
        for component in components:
            dep_statuses = tuple(
                dependencies[dep] for dep in component.dependencies if dep in dependencies
            )
            try:
                state, message = component.check_fn()
                if not isinstance(state, HealthState):
                    state = HealthState.UNKNOWN
                    message = "Invalid health check result"
            except Exception as error:
                state = HealthState.UNHEALTHY
                message = str(error)
            results.append(
                ComponentHealth(
                    name=component.name,
                    state=state,
                    message=message,
                    dependencies=dep_statuses,
                )
            )
        return tuple(results)
