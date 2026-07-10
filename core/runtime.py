"""Core runtime integration."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from config.hash import compute_configuration_hash
from config.settings import CoreSettings, get_settings
from core.context.audit_context import AuditContext
from core.context.core_context import CoreContext
from core.context.execution_context import ExecutionContext
from core.context.identity_context import IdentityContext
from core.context.operation_context import OperationContext
from core.context.request_context import RequestContext
from core.context.security_context import SecurityContext
from core.errors.exceptions import CoreContextError
from core.events.domain_events import CoreDomainEvent, CoreDomainEventType
from core.lifecycle import CoreLifecycleEventType, CoreLifecycleManager
from health.models import HealthState
from models.events import DomainEvent, EventType
from pipeline.context import PipelineContext, build_pipeline_context

_default_runtime: CoreRuntime | None = None
_runtime_lock = RLock()


class CoreRuntime:
    """Coordinates core context propagation and observability integration."""

    def __init__(
        self,
        *,
        context: PipelineContext | None = None,
        settings: CoreSettings | None = None,
        lifecycle: CoreLifecycleManager | None = None,
    ) -> None:
        self._context = context or build_pipeline_context()
        self._settings = settings or get_settings().core
        self._lifecycle = lifecycle or CoreLifecycleManager(self._context)
        self._active_context: CoreContext | None = None

    @property
    def pipeline_context(self) -> PipelineContext:
        return self._context

    @property
    def lifecycle(self) -> CoreLifecycleManager:
        return self._lifecycle

    @property
    def active_context(self) -> CoreContext | None:
        return self._active_context

    def initialize(self) -> CoreContext:
        """Initialize the core runtime and create a root context."""
        trace_id = str(uuid4())
        correlation_id = str(uuid4())
        request_id = str(uuid4())
        execution_id = str(uuid4())
        operation_id = str(uuid4())
        audit_id = str(uuid4())

        core_context = CoreContext(
            trace_id=trace_id,
            correlation_id=correlation_id,
            request=RequestContext(request_id=request_id),
            execution=ExecutionContext(
                execution_id=execution_id,
                configuration_hash=compute_configuration_hash(),
                schema_version=self._context.settings.schema_version,
                feature_flags=self._context.application.feature_flags.all_flags(),
            ),
            operation=OperationContext(
                operation_id=operation_id,
                operation_type="runtime_initialize",
            ),
            identity=IdentityContext(),
            security=SecurityContext(),
            audit=AuditContext(
                audit_id=audit_id,
                action="runtime_initialize",
                resource_type="core_runtime",
                resource_id="core",
            ),
        )
        self._active_context = core_context
        self._context.health.register(
            "core.runtime",
            lambda: self._health_check(),
            dependencies=(),
        )
        self._context.metrics.gauge("core.runtime.active").set(1.0)
        self._lifecycle.emit(
            CoreLifecycleEventType.RUNTIME_INITIALIZED,
            entity_id="core",
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="Core runtime initialized",
        )
        self._write_audit(core_context, action="runtime_initialize")
        return core_context

    def build_context(
        self,
        *,
        operation_type: str,
        dataset_ids: tuple[str, ...] = (),
        plugin_ids: tuple[str, ...] = (),
        principal_id: str = "system",
        parent: CoreContext | None = None,
    ) -> CoreContext:
        """Build an operation-scoped core context."""
        if not self._settings.context_enabled:
            msg = "Core context propagation is disabled"
            raise CoreContextError(msg)

        parent_context = parent or self._active_context
        trace_id = parent_context.trace_id if parent_context is not None else str(uuid4())
        correlation_id = (
            parent_context.correlation_id if parent_context is not None else str(uuid4())
        )

        core_context = CoreContext(
            trace_id=trace_id,
            correlation_id=correlation_id,
            request=RequestContext(
                request_id=str(uuid4()),
                source=parent_context.request.source if parent_context else "platform",
            ),
            execution=ExecutionContext(
                execution_id=str(uuid4()),
                configuration_hash=compute_configuration_hash(),
                schema_version=self._context.settings.schema_version,
                feature_flags=self._context.application.feature_flags.all_flags(),
            ),
            operation=OperationContext(
                operation_id=str(uuid4()),
                operation_type=operation_type,
                parent_operation_id=(
                    parent_context.operation.operation_id if parent_context else None
                ),
            ),
            identity=IdentityContext(principal_id=principal_id),
            security=SecurityContext(),
            audit=AuditContext(
                audit_id=str(uuid4()),
                actor_id=principal_id,
                action=operation_type,
                resource_type="core_operation",
                resource_id=operation_type,
                dataset_ids=dataset_ids,
                plugin_ids=plugin_ids,
            ),
            dataset_ids=dataset_ids,
            plugin_ids=plugin_ids,
        )
        self._active_context = core_context
        self._lifecycle.emit(
            CoreLifecycleEventType.CONTEXT_CREATED,
            entity_id=operation_type,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=f"Core context created for {operation_type}",
        )
        self._write_audit(core_context, action=operation_type)
        return core_context

    def publish_domain_event(self, event: CoreDomainEvent) -> None:
        """Publish a core domain event to the platform EventBus."""
        event_type_map = {
            CoreDomainEventType.DATASET_LOADED: EventType.VALIDATION_COMPLETED,
            CoreDomainEventType.RESOURCE_CREATED: EventType.PREDICTION_CREATED,
            CoreDomainEventType.EVALUATION_COMPLETED: EventType.VALIDATION_COMPLETED,
            CoreDomainEventType.DECISION_GENERATED: EventType.DECISION_CREATED,
        }
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=event_type_map[event.event_type],
            correlation_id=event.correlation_id,
            market_id="platform",
            symbol_id=event.entity_id,
            payload={
                "source": "core",
                "core_event_type": event.event_type.value,
                "trace_id": event.trace_id,
                **event.payload,
            },
        )
        self._context.event_bus.publish(domain_event)
        self._context.metrics.counter(f"core.domain.{event.event_type.value}").inc(1)

    def shutdown(self) -> None:
        """Shutdown the core runtime and clear active context."""
        if self._active_context is None:
            return
        trace_id = self._active_context.trace_id
        correlation_id = self._active_context.correlation_id
        self._lifecycle.emit(
            CoreLifecycleEventType.RUNTIME_SHUTDOWN,
            entity_id="core",
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="Core runtime shutdown",
        )
        self._context.metrics.gauge("core.runtime.active").set(0.0)
        self._active_context = None

    def _health_check(self) -> tuple[HealthState, str]:
        if self._active_context is None:
            return HealthState.UNHEALTHY, "core runtime is not initialized"
        return HealthState.HEALTHY, "core runtime is active"

    def _write_audit(self, core_context: CoreContext, *, action: str) -> None:
        if not self._settings.audit_enabled:
            return
        core_context.audit.attributes["action_recorded"] = action


def get_core_runtime() -> CoreRuntime:
    """Return the process-wide default core runtime."""
    global _default_runtime
    with _runtime_lock:
        if _default_runtime is None:
            _default_runtime = CoreRuntime()
        return _default_runtime


def reset_core_runtime() -> None:
    """Reset the default core runtime. Intended for tests."""
    global _default_runtime
    with _runtime_lock:
        _default_runtime = None
