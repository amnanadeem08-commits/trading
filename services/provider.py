"""Service provider for wiring and observability registration."""

from __future__ import annotations

from models.common import VersionInfo
from services.container import ServiceContainer
from services.context import ApplicationContext
from services.lifecycle import LifecycleManager
from services.registry import ServiceRegistry
from services.service import BaseService


class ServiceProvider:
    """Provides services through constructor-based dependency injection."""

    def __init__(
        self,
        container: ServiceContainer,
        registry: ServiceRegistry,
        context: ApplicationContext,
        lifecycle: LifecycleManager | None = None,
    ) -> None:
        self._container = container
        self._registry = registry
        self._context = context
        self._lifecycle = lifecycle

    @property
    def container(self) -> ServiceContainer:
        return self._container

    @property
    def registry(self) -> ServiceRegistry:
        return self._registry

    @property
    def context(self) -> ApplicationContext:
        return self._context

    def provide(self, service_type: type[BaseService]) -> BaseService:
        """Resolve and register a service with observability hooks."""
        service = self._container.resolve(service_type)
        return self.wire(service)

    def wire(self, service: BaseService) -> BaseService:
        """Register an existing service instance with observability hooks."""
        self._registry.register(service)
        self.register_observability(service)
        if self._lifecycle is not None:
            self._lifecycle.emit_registered(service)
        return service

    def register_observability(self, service: BaseService) -> None:
        """Register a service with health, metrics, logging, and version tracking."""
        service_name = service.name()
        self._context.health.register(
            service_name,
            lambda: (service.status(), "service status"),
            dependencies=service.dependencies(),
        )
        self._context.metrics.gauge(f"service.{service_name}.ready").set(
            1.0 if service.ready() else 0.0
        )
        self._context.metrics.counter(f"service.{service_name}.lifecycle").inc(0)
        self._context.logger_factory.create(service_name=service_name)
        version_id = service.version()
        if not self._context.version_registry.services.exists(version_id):
            self._context.version_registry.services.register(
                VersionInfo(version_id=version_id, description=service_name),
            )
