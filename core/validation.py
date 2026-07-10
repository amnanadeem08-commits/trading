"""Core entity validation."""

from __future__ import annotations

from dataclasses import dataclass

from core.dependency import build_dependency_graph, detect_cycle, topological_order
from core.entities.entity import Entity
from core.errors.exceptions import CircularEntityDependencyError


@dataclass(frozen=True)
class CoreValidationResult:
    """Outcome of core entity validation."""

    valid: bool
    errors: tuple[str, ...] = ()
    load_order: tuple[str, ...] = ()


def _entities_by_id(entities: tuple[Entity, ...]) -> dict[str, Entity]:
    return {entity.entity_id: entity for entity in entities}


def _dependency_map(entities: dict[str, Entity]) -> dict[str, tuple[str, ...]]:
    return {entity_id: entity.dependencies for entity_id, entity in entities.items()}


def validate_entity_set(entities: tuple[Entity, ...]) -> CoreValidationResult:
    """Validate a set of core entities."""
    errors: list[str] = []
    entity_map = _entities_by_id(entities)
    entity_ids = [entity.entity_id for entity in entities]
    if len(entity_ids) != len(set(entity_ids)):
        errors.append("Duplicate entity identifiers detected")

    for entity in entities:
        if not entity.entity_id.strip():
            errors.append("Entity id must not be empty")
        if not entity.entity_type.strip():
            errors.append(f"Entity type must not be empty: {entity.entity_id}")
        for dependency in entity.dependencies:
            if dependency == entity.entity_id:
                errors.append(f"Entity depends on itself: {entity.entity_id}")
            elif dependency not in entity_map:
                errors.append(
                    f"Missing dependency '{dependency}' required by '{entity.entity_id}'",
                )

    if errors:
        return CoreValidationResult(valid=False, errors=tuple(errors))

    graph = build_dependency_graph(tuple(entity_map.keys()), _dependency_map(entity_map))
    cycle = detect_cycle(graph)
    if cycle is not None:
        raise CircularEntityDependencyError(cycle)

    return CoreValidationResult(
        valid=True,
        load_order=topological_order(graph),
    )


def validate_entity(entity: Entity) -> CoreValidationResult:
    """Validate a single entity definition."""
    return validate_entity_set((entity,))
