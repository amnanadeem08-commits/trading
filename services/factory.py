"""Service factory for creating configured service instances."""

from __future__ import annotations

from collections.abc import Callable

from services.container import ServiceContainer
from services.context import ApplicationContext, build_application_context
from services.lifecycle import LifecycleManager
from services.provider import ServiceProvider
from services.registry import ServiceRegistry
from services.service import BaseService


class ServiceFactory:
    """Creates services using dependency injection and registration hooks."""

    def __init__(
        self,
        container: ServiceContainer,
        provider: ServiceProvider,
        context: ApplicationContext,
        lifecycle: LifecycleManager,
    ) -> None:
        self._container = container
        self._provider = provider
        self._context = context
        self._lifecycle = lifecycle

    @property
    def context(self) -> ApplicationContext:
        return self._context

    @property
    def lifecycle(self) -> LifecycleManager:
        return self._lifecycle

    @property
    def registry(self) -> ServiceRegistry:
        return self._provider.registry

    def register_type(
        self,
        service_type: type[BaseService],
        factory: Callable[..., BaseService] | None = None,
        *,
        singleton: bool = True,
    ) -> None:
        """Register a service type with the container."""
        if factory is not None:
            self._container.register_factory(service_type, factory, singleton=singleton)
            return
        self._container.register_type(service_type, singleton=singleton)

    def create(self, service_type: type[BaseService]) -> BaseService:
        """Create and register a service instance."""
        return self._provider.provide(service_type)

    def create_from_instance(self, service: BaseService) -> BaseService:
        """Register a pre-built service instance."""
        return self._provider.wire(service)


def build_service_factory(context: ApplicationContext | None = None) -> ServiceFactory:
    """Build a service factory with default container, registry, and provider."""
    resolved_context = context or build_application_context()
    registry = ServiceRegistry()
    container = ServiceContainer()
    lifecycle = LifecycleManager(
        registry,
        resolved_context,
        resolved_context.settings.services,
    )
    provider = ServiceProvider(container, registry, resolved_context, lifecycle)
    return ServiceFactory(container, provider, resolved_context, lifecycle)
