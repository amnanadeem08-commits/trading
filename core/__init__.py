"""Core layer public API."""

from core.context.audit_context import AuditContext
from core.context.core_context import CoreContext
from core.context.execution_context import ExecutionContext
from core.context.identity_context import IdentityContext
from core.context.operation_context import OperationContext
from core.context.request_context import RequestContext
from core.context.security_context import SecurityContext
from core.contracts.result import OperationResult, ResultStatus
from core.decorators import entity, entity_metadata
from core.dependency import DependencyGraph, build_dependency_graph, detect_cycle, topological_order
from core.entities.entity import BaseEntity, Entity
from core.errors.exceptions import (
    CircularEntityDependencyError,
    CoreContextError,
    CoreError,
    CoreRuntimeError,
    CoreStateError,
    CoreValidationError,
    EntityNotFoundError,
    EntityRegistrationError,
    IdentifierError,
)
from core.events.domain_events import (
    CoreDomainEvent,
    CoreDomainEventType,
    DatasetLoadedEvent,
    DecisionGeneratedEvent,
    EvaluationCompletedEvent,
    ResourceCreatedEvent,
)
from core.identifiers.id_manager import EntityId, IdManager, generate_entity_id, validate_entity_id
from core.lifecycle import CoreLifecycleEvent, CoreLifecycleEventType, CoreLifecycleManager
from core.registry import EntityRegistry, get_entity_registry, reset_entity_registry
from core.runtime import CoreRuntime, get_core_runtime, reset_core_runtime
from core.state.operation_state import TERMINAL_OPERATION_STATES, OperationState
from core.validation import CoreValidationResult, validate_entity, validate_entity_set

__all__ = [
    "TERMINAL_OPERATION_STATES",
    "AuditContext",
    "BaseEntity",
    "CircularEntityDependencyError",
    "CoreContext",
    "CoreContextError",
    "CoreDomainEvent",
    "CoreDomainEventType",
    "CoreError",
    "CoreLifecycleEvent",
    "CoreLifecycleEventType",
    "CoreLifecycleManager",
    "CoreRuntime",
    "CoreRuntimeError",
    "CoreStateError",
    "CoreValidationError",
    "CoreValidationResult",
    "DatasetLoadedEvent",
    "DecisionGeneratedEvent",
    "DependencyGraph",
    "Entity",
    "EntityId",
    "EntityNotFoundError",
    "EntityRegistrationError",
    "EntityRegistry",
    "EvaluationCompletedEvent",
    "ExecutionContext",
    "IdManager",
    "IdentifierError",
    "IdentityContext",
    "OperationContext",
    "OperationResult",
    "OperationState",
    "RequestContext",
    "ResourceCreatedEvent",
    "ResultStatus",
    "SecurityContext",
    "build_dependency_graph",
    "detect_cycle",
    "entity",
    "entity_metadata",
    "generate_entity_id",
    "get_core_runtime",
    "get_entity_registry",
    "reset_core_runtime",
    "reset_entity_registry",
    "topological_order",
    "validate_entity",
    "validate_entity_id",
    "validate_entity_set",
]
