"""Automatic service discovery."""

from __future__ import annotations

import importlib
import inspect
import pkgutil
from types import ModuleType

from services.decorators import service_metadata
from services.exceptions import ServiceRegistrationError
from services.registry import ServiceRegistry
from services.service import BaseService


class ServiceDiscovery:
    """Discovers service classes and registers them automatically."""

    def __init__(self, package_name: str = "services") -> None:
        self._package_name = package_name

    def discover(self, modules: tuple[str, ...] | None = None) -> tuple[type[BaseService], ...]:
        """Discover service classes from configured modules."""
        discovered: list[type[BaseService]] = []
        module_names = modules or self._discover_module_names()
        for module_name in module_names:
            module = importlib.import_module(module_name)
            discovered.extend(self._discover_in_module(module))
        return tuple(discovered)

    def register_discovered(
        self,
        registry: ServiceRegistry,
        *,
        modules: tuple[str, ...] | None = None,
    ) -> tuple[str, ...]:
        """Discover and register services that opt into auto-registration."""
        registered: list[str] = []
        for service_type in self.discover(modules=modules):
            metadata = service_metadata(service_type)
            if not metadata.get("auto_register", False):
                continue
            instance = service_type()
            registry.register(instance)
            registered.append(instance.name())
        return tuple(registered)

    def _discover_module_names(self) -> tuple[str, ...]:
        package = importlib.import_module(self._package_name)
        if not hasattr(package, "__path__"):
            return (self._package_name,)
        names: list[str] = []
        for module_info in pkgutil.iter_modules(package.__path__, prefix=f"{self._package_name}."):
            if module_info.name.endswith(".tests"):
                continue
            names.append(module_info.name)
        return tuple(sorted(names))

    def _discover_in_module(self, module: ModuleType) -> tuple[type[BaseService], ...]:
        discovered: list[type[BaseService]] = []
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__:
                continue
            if not issubclass(obj, BaseService) or obj is BaseService:
                continue
            if inspect.isabstract(obj):
                continue
            discovered.append(obj)
        return tuple(discovered)


def discover_service_types(modules: tuple[str, ...] | None = None) -> tuple[type[BaseService], ...]:
    """Discover service classes using the default discovery configuration."""
    return ServiceDiscovery().discover(modules=modules)


def ensure_concrete_service(service_type: type[BaseService]) -> None:
    """Validate that a discovered service can be instantiated."""
    if inspect.isabstract(service_type):
        msg = f"Cannot instantiate abstract service: {service_type.__name__}"
        raise ServiceRegistrationError(msg)
