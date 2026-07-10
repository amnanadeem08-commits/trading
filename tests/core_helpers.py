"""Helpers for core layer tests."""

from __future__ import annotations

from core.decorators import entity
from core.entities.entity import BaseEntity, Entity
from core.state.operation_state import OperationState


def make_entity(
    *,
    entity_id: str = "sample-entity",
    name: str = "Sample Entity",
    version: str = "1.0.0",
    entity_type: str = "resource",
    dependencies: tuple[str, ...] = (),
    state: OperationState = OperationState.REGISTERED,
) -> Entity:
    return Entity(
        entity_id=entity_id,
        name=name,
        version=version,
        entity_type=entity_type,
        state=state,
        dependencies=dependencies,
        metadata={"scope": "test"},
    )


@entity(entity_id="sample-entity", auto_register=False)
class SampleEntity(BaseEntity):
    """Concrete entity used in unit tests."""

    def entity_id(self) -> str:
        return "sample-entity"

    def name(self) -> str:
        return "Sample Entity"

    def version(self) -> str:
        return "1.0.0"

    def entity_type(self) -> str:
        return "resource"

    def metadata(self) -> dict[str, str]:
        return {"scope": "test"}


@entity(entity_id="derived-entity", auto_register=False)
class DerivedEntity(BaseEntity):
    """Entity with a dependency on sample-entity."""

    def entity_id(self) -> str:
        return "derived-entity"

    def name(self) -> str:
        return "Derived Entity"

    def version(self) -> str:
        return "1.0.0"

    def entity_type(self) -> str:
        return "resource"

    def dependencies(self) -> tuple[str, ...]:
        return ("sample-entity",)
