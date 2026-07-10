"""Service startup and shutdown lifecycle management."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from threading import RLock
from uuid import uuid4

from config.settings import ServiceSettings
from health.checks import CheckOutcome, CheckResult
from models.common import PlatformModel, UTCDateTime, utc_now
from services.context import ApplicationContext
from services.exceptions import ServiceLifecycleError, ServiceNotReadyError
from services.registry import ServiceRegistry
from services.service import BaseService, ServiceState
from services.validation import ValidationResult

type LifecycleHandler = Callable[["ServiceLifecycleEvent"], None]


class LifecycleEventType(StrEnum):
    """Lifecycle event identifiers."""

    SERVICE_REGISTERED = "service_registered"
    SERVICE_STARTED = "service_started"
    SERVICE_STOPPED = "service_stopped"
    SERVICE_FAILED = "service_failed"


class ServiceLifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the service layer."""

    event_id: str
    event_type: LifecycleEventType
    service_name: str
    service_version: str
    message: str
    occurred_at: UTCDateTime


@dataclass(frozen=True)
class LifecycleOperationResult:
    """Result of a startup or shutdown operation."""

    service_name: str
    success: bool
    message: str
    check: CheckResult | None = None


@dataclass(frozen=True)
class LifecycleSequenceResult:
    """Aggregate result for lifecycle sequencing."""

    success: bool
    operations: tuple[LifecycleOperationResult, ...]
    order: tuple[str, ...] = ()


class LifecycleManager:
    """Coordinates startup and shutdown with dependency ordering."""

    def __init__(
        self,
        registry: ServiceRegistry,
        context: ApplicationContext,
        settings: ServiceSettings,
    ) -> None:
        self._registry = registry
        self._context = context
        self._settings = settings
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[ServiceLifecycleEvent] = []
        self._states: dict[str, ServiceState] = {}

    @property
    def events(self) -> tuple[ServiceLifecycleEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def on_event(self, handler: LifecycleHandler) -> str:
        """Subscribe to lifecycle events. Returns subscription id."""
        subscription_id = str(uuid4())
        with self._lock:
            self._handlers[subscription_id] = handler
        return subscription_id

    def off_event(self, subscription_id: str) -> None:
        with self._lock:
            self._handlers.pop(subscription_id, None)

    def startup(self, services: tuple[str, ...] | None = None) -> LifecycleSequenceResult:
        """Start services in dependency order with validation."""
        validation = self._validate_for_lifecycle()
        order = self._resolve_order(validation.startup_order, services)
        operations: list[LifecycleOperationResult] = []
        for service_name in order:
            service = self._registry.resolve(service_name)
            for dependency in service.dependencies():
                dependency_state = self._states.get(dependency, ServiceState.REGISTERED)
                if dependency_state != ServiceState.RUNNING:
                    result = LifecycleOperationResult(
                        service_name=service_name,
                        success=False,
                        message=f"Dependency not running: {dependency}",
                    )
                    operations.append(result)
                    self._emit_failure(service, result.message)
                    return LifecycleSequenceResult(
                        success=False,
                        operations=tuple(operations),
                        order=order,
                    )
            try:
                self._states[service_name] = ServiceState.STARTING
                service.start()
                self._states[service_name] = ServiceState.RUNNING
                self._context.metrics.gauge(f"service.{service_name}.ready").set(
                    1.0 if service.ready() else 0.0
                )
                self._context.metrics.counter(f"service.{service_name}.lifecycle").inc(1)
                if not service.ready():
                    raise ServiceNotReadyError(service_name)
                check = CheckResult(
                    name=f"startup:{service_name}",
                    outcome=CheckOutcome.PASSED,
                    message="started",
                )
                operations.append(
                    LifecycleOperationResult(
                        service_name=service_name,
                        success=True,
                        message="started",
                        check=check,
                    )
                )
                self._emit_event(
                    LifecycleEventType.SERVICE_STARTED,
                    service,
                    message="started",
                )
            except Exception as error:
                self._states[service_name] = ServiceState.FAILED
                result = LifecycleOperationResult(
                    service_name=service_name,
                    success=False,
                    message=str(error),
                    check=CheckResult(
                        name=f"startup:{service_name}",
                        outcome=CheckOutcome.FAILED,
                        message=str(error),
                    ),
                )
                operations.append(result)
                self._emit_failure(service, str(error))
                return LifecycleSequenceResult(
                    success=False,
                    operations=tuple(operations),
                    order=order,
                )
        return LifecycleSequenceResult(success=True, operations=tuple(operations), order=order)

    def shutdown(self, services: tuple[str, ...] | None = None) -> LifecycleSequenceResult:
        """Stop services in reverse dependency order with graceful validation."""
        validation = self._validate_for_lifecycle()
        order = self._resolve_order(validation.shutdown_order, services)
        operations: list[LifecycleOperationResult] = []
        for service_name in order:
            if not self._registry.exists(service_name):
                continue
            service = self._registry.resolve(service_name)
            current_state = self._states.get(service_name, ServiceState.REGISTERED)
            active_states = {
                ServiceState.RUNNING,
                ServiceState.STARTING,
                ServiceState.FAILED,
            }
            if current_state not in active_states:
                operations.append(
                    LifecycleOperationResult(
                        service_name=service_name,
                        success=True,
                        message="already stopped",
                    )
                )
                continue
            try:
                self._states[service_name] = ServiceState.STOPPING
                service.stop()
                self._states[service_name] = ServiceState.STOPPED
                self._context.metrics.gauge(f"service.{service_name}.ready").set(0.0)
                check = CheckResult(
                    name=f"shutdown:{service_name}",
                    outcome=CheckOutcome.PASSED,
                    message="stopped",
                )
                operations.append(
                    LifecycleOperationResult(
                        service_name=service_name,
                        success=True,
                        message="stopped",
                        check=check,
                    )
                )
                self._emit_event(
                    LifecycleEventType.SERVICE_STOPPED,
                    service,
                    message="stopped",
                )
            except Exception as error:
                self._states[service_name] = ServiceState.FAILED
                result = LifecycleOperationResult(
                    service_name=service_name,
                    success=False,
                    message=str(error),
                    check=CheckResult(
                        name=f"shutdown:{service_name}",
                        outcome=CheckOutcome.FAILED,
                        message=str(error),
                    ),
                )
                operations.append(result)
                self._emit_failure(service, str(error))
                if not self._settings.graceful_shutdown:
                    return LifecycleSequenceResult(
                        success=False,
                        operations=tuple(operations),
                        order=order,
                    )
        success = all(operation.success for operation in operations)
        return LifecycleSequenceResult(success=success, operations=tuple(operations), order=order)

    def emit_registered(self, service: BaseService) -> None:
        """Emit a service registered lifecycle event."""
        self._states[service.name()] = ServiceState.REGISTERED
        self._emit_event(
            LifecycleEventType.SERVICE_REGISTERED,
            service,
            message="registered",
        )

    def _validate_for_lifecycle(self) -> ValidationResult:
        validation = self._registry.validate()
        if not validation.valid:
            msg = "Service graph validation failed"
            raise ServiceLifecycleError(msg)
        return validation

    def _resolve_order(
        self,
        computed_order: tuple[str, ...],
        requested: tuple[str, ...] | None,
    ) -> tuple[str, ...]:
        if requested is None:
            return computed_order
        requested_set = set(requested)
        return tuple(name for name in computed_order if name in requested_set)

    def _emit_event(
        self,
        event_type: LifecycleEventType,
        service: BaseService,
        *,
        message: str,
    ) -> None:
        event = ServiceLifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            service_name=service.name(),
            service_version=service.version(),
            message=message,
            occurred_at=utc_now(),
        )
        with self._lock:
            self._events.append(event)
            handlers = tuple(self._handlers.values())
        for handler in handlers:
            handler(event)

    def _emit_failure(self, service: BaseService, message: str) -> None:
        self._emit_event(LifecycleEventType.SERVICE_FAILED, service, message=message)
