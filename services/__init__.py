"""Platform service layer."""

from services.container import ServiceContainer
from services.context import (
    ApplicationContext,
    LoggerFactory,
    VersionRegistry,
    build_application_context,
    reset_application_context,
)
from services.decorators import service, service_metadata
from services.discovery import ServiceDiscovery, discover_service_types, ensure_concrete_service
from services.exceptions import (
    CircularDependencyError,
    ServiceError,
    ServiceLifecycleError,
    ServiceNotFoundError,
    ServiceNotReadyError,
    ServiceRegistrationError,
    ServiceResolutionError,
    ServiceValidationError,
)
from services.factory import ServiceFactory, build_service_factory
from services.lifecycle import (
    LifecycleEventType,
    LifecycleManager,
    LifecycleOperationResult,
    LifecycleSequenceResult,
    ServiceLifecycleEvent,
)
from services.provider import ServiceProvider
from services.registry import ServiceRegistry, get_service_registry, reset_service_registry
from services.service import BaseService, ServiceState
from services.validation import ValidationResult, validate_services

__all__ = [
    "ApplicationContext",
    "BaseService",
    "CircularDependencyError",
    "LifecycleEventType",
    "LifecycleManager",
    "LifecycleOperationResult",
    "LifecycleSequenceResult",
    "LoggerFactory",
    "ServiceContainer",
    "ServiceDiscovery",
    "ServiceError",
    "ServiceFactory",
    "ServiceLifecycleError",
    "ServiceLifecycleEvent",
    "ServiceNotFoundError",
    "ServiceNotReadyError",
    "ServiceProvider",
    "ServiceRegistrationError",
    "ServiceRegistry",
    "ServiceResolutionError",
    "ServiceState",
    "ServiceValidationError",
    "ValidationResult",
    "VersionRegistry",
    "build_application_context",
    "build_service_factory",
    "discover_service_types",
    "ensure_concrete_service",
    "get_service_registry",
    "reset_application_context",
    "reset_service_registry",
    "service",
    "service_metadata",
    "validate_services",
]
