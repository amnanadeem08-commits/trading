"""Core entity registration decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from core.entities.entity import BaseEntity

EntityType = TypeVar("EntityType", bound=BaseEntity)

_ENTITY_METADATA_KEY = "_platform_entity_metadata"


def entity(
    *,
    entity_id: str | None = None,
    auto_register: bool = True,
) -> Callable[[EntityType], EntityType]:
    """Attach discovery metadata to an entity implementation."""

    def decorator(defn: EntityType) -> EntityType:
        setattr(
            defn,
            _ENTITY_METADATA_KEY,
            {
                "entity_id": entity_id,
                "auto_register": auto_register,
            },
        )
        return defn

    return decorator


def entity_metadata(defn: type[BaseEntity] | BaseEntity) -> dict[str, str | bool | None]:
    """Return discovery metadata attached to an entity implementation."""
    metadata = getattr(defn, _ENTITY_METADATA_KEY, None)
    if metadata is None:
        return {"entity_id": None, "auto_register": False}
    return dict(metadata)
