"""Service registry."""

from __future__ import annotations

from threading import RLock

from services.exceptions import ServiceNotFoundError, ServiceRegistrationError
from services.service import BaseService
from services.validation import ValidationResult, validate_services

_default_registry: ServiceRegistry | None = None
_registry_lock = RLock()


class ServiceRegistry:
    """Thread-safe registry for platform services."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._services: dict[str, BaseService] = {}

    def register(self, service: BaseService) -> None:
        """Register a service instance."""
        name = service.name()
        if not name.strip():
            msg = "Service name must not be empty"
            raise ServiceRegistrationError(msg)
        with self._lock:
            if name in self._services:
                msg = f"Service already registered: {name}"
                raise ServiceRegistrationError(msg)
            self._services[name] = service

    def unregister(self, name: str) -> None:
        """Remove a service registration."""
        with self._lock:
            if name not in self._services:
                raise ServiceNotFoundError(name)
            del self._services[name]

    def resolve(self, name: str) -> BaseService:
        """Resolve a service by name."""
        with self._lock:
            service = self._services.get(name)
        if service is None:
            raise ServiceNotFoundError(name)
        return service

    def exists(self, name: str) -> bool:
        with self._lock:
            return name in self._services

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._services.keys()))

    def validate(self) -> ValidationResult:
        """Validate the registered service graph."""
        with self._lock:
            services = dict(self._services)
        return validate_services(services)


def get_service_registry() -> ServiceRegistry:
    """Return the process-wide default service registry."""
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = ServiceRegistry()
        return _default_registry


def reset_service_registry() -> None:
    """Reset the default service registry. Intended for tests."""
    global _default_registry
    with _registry_lock:
        _default_registry = None
