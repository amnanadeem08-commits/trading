"""Core entity registry."""

from __future__ import annotations

from threading import RLock

from core.entities.entity import BaseEntity, Entity
from core.errors.exceptions import EntityNotFoundError, EntityRegistrationError
from core.validation import CoreValidationResult, validate_entity, validate_entity_set

_default_registry: EntityRegistry | None = None
_registry_lock = RLock()


class EntityRegistry:
    """Thread-safe registry for core entity definitions and types."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entities: dict[str, Entity] = {}
        self._types: dict[str, type[BaseEntity]] = {}

    def register(self, entity: Entity) -> None:
        """Register an entity definition."""
        entity_id = entity.entity_id
        if not entity_id.strip():
            msg = "Entity id must not be empty"
            raise EntityRegistrationError(msg)
        with self._lock:
            if entity_id in self._entities:
                msg = f"Entity already registered: {entity_id}"
                raise EntityRegistrationError(msg)
            self._entities[entity_id] = entity

    def unregister(self, entity_id: str) -> None:
        with self._lock:
            if entity_id not in self._entities:
                raise EntityNotFoundError(entity_id)
            del self._entities[entity_id]

    def register_type(self, entity_type: type[BaseEntity]) -> None:
        """Register an entity implementation type."""
        instance = entity_type()
        entity_id = instance.entity_id()
        with self._lock:
            self._types[entity_id] = entity_type

    def unregister_type(self, entity_id: str) -> None:
        with self._lock:
            if entity_id not in self._types:
                raise EntityNotFoundError(entity_id)
            del self._types[entity_id]

    def resolve(self, entity_id: str) -> Entity:
        """Resolve a registered entity by identifier."""
        with self._lock:
            entity = self._entities.get(entity_id)
        if entity is None:
            raise EntityNotFoundError(entity_id)
        return entity

    def resolve_type(self, entity_id: str) -> type[BaseEntity]:
        """Resolve a registered entity type by identifier."""
        with self._lock:
            entity_type = self._types.get(entity_id)
        if entity_type is None:
            raise EntityNotFoundError(entity_id)
        return entity_type

    def exists(self, entity_id: str) -> bool:
        with self._lock:
            return entity_id in self._entities

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._entities.keys()))

    def list_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._types.keys()))

    def validate(self, entity: Entity) -> CoreValidationResult:
        """Validate a single entity definition."""
        return validate_entity(entity)

    def validate_set(self, entities: tuple[Entity, ...] | None = None) -> CoreValidationResult:
        """Validate registered entities or a provided set."""
        if entities is None:
            with self._lock:
                entities = tuple(self._entities.values())
        return validate_entity_set(entities)


def get_entity_registry() -> EntityRegistry:
    """Return the process-wide default entity registry."""
    global _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = EntityRegistry()
        return _default_registry


def reset_entity_registry() -> None:
    """Reset the default entity registry. Intended for tests."""
    global _default_registry
    with _registry_lock:
        _default_registry = None
