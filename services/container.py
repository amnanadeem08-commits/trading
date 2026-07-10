"""Dependency injection container."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from threading import RLock
from typing import Any, get_type_hints

from services.exceptions import ServiceResolutionError
from services.service import BaseService


class ServiceContainer:
    """Constructor-based dependency injection container."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._factories: dict[type[BaseService], Callable[..., BaseService]] = {}
        self._instances: dict[type[BaseService], BaseService] = {}
        self._singletons: set[type[BaseService]] = set()

    def register_factory(
        self,
        service_type: type[BaseService],
        factory: Callable[..., BaseService],
        *,
        singleton: bool = True,
    ) -> None:
        """Register a factory for a service type."""
        with self._lock:
            self._factories[service_type] = factory
            if singleton:
                self._singletons.add(service_type)
            else:
                self._singletons.discard(service_type)
            self._instances.pop(service_type, None)

    def register_instance(self, service_type: type[BaseService], instance: BaseService) -> None:
        """Register a pre-built service instance."""
        with self._lock:
            self._instances[service_type] = instance
            self._singletons.add(service_type)

    def register_type(self, service_type: type[BaseService], *, singleton: bool = True) -> None:
        """Mark a service type for constructor-based resolution."""
        with self._lock:
            if singleton:
                self._singletons.add(service_type)

    def resolve(self, service_type: type[BaseService]) -> BaseService:
        """Resolve a service by type using constructor injection."""
        with self._lock:
            if service_type in self._instances:
                return self._instances[service_type]
            factory = self._factories.get(service_type)
            if factory is None:
                if inspect.isclass(service_type) and issubclass(service_type, BaseService):
                    instance = self._construct(service_type)
                    if service_type in self._singletons or service_type not in self._factories:
                        self._instances[service_type] = instance
                    return instance
                msg = f"No factory registered for service type: {service_type.__name__}"
                raise ServiceResolutionError(msg)
            instance = factory()
            if service_type in self._singletons:
                self._instances[service_type] = instance
            return instance

    def clear(self) -> None:
        """Clear all registrations."""
        with self._lock:
            self._factories.clear()
            self._instances.clear()
            self._singletons.clear()

    def registered_types(self) -> tuple[type[BaseService], ...]:
        with self._lock:
            keys = set(self._factories.keys()) | set(self._instances.keys())
            return tuple(sorted(keys, key=lambda item: item.__name__))

    def _construct(self, service_type: type[BaseService]) -> BaseService:
        signature = inspect.signature(service_type.__init__)
        try:
            type_hints = get_type_hints(service_type.__init__)
        except NameError as error:
            msg = f"Cannot resolve constructor annotations for {service_type.__name__}"
            raise ServiceResolutionError(msg) from error
        kwargs: dict[str, Any] = {}
        for parameter_name, parameter in signature.parameters.items():
            if parameter_name == "self":
                continue
            if parameter.kind in {
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            }:
                continue
            if parameter_name not in type_hints:
                if parameter.default is inspect.Parameter.empty:
                    msg = (
                        f"Cannot resolve constructor parameter '{parameter_name}' "
                        f"for {service_type.__name__}"
                    )
                    raise ServiceResolutionError(msg)
                continue
            dependency_type = type_hints[parameter_name]
            if not inspect.isclass(dependency_type):
                if parameter.default is inspect.Parameter.empty:
                    msg = (
                        f"Unsupported constructor annotation for '{parameter_name}' "
                        f"on {service_type.__name__}"
                    )
                    raise ServiceResolutionError(msg)
                continue
            if issubclass(dependency_type, BaseService):
                kwargs[parameter_name] = self.resolve(dependency_type)
                continue
            if parameter.default is inspect.Parameter.empty:
                msg = (
                    f"Cannot resolve constructor parameter '{parameter_name}' "
                    f"for {service_type.__name__}"
                )
                raise ServiceResolutionError(msg)
        return service_type(**kwargs)
