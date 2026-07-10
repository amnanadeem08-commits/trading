"""Entity identifier management."""

from __future__ import annotations

import re
from uuid import uuid4

from pydantic import Field

from core.errors.exceptions import IdentifierError
from models.common import PlatformModel

_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")


class EntityId(PlatformModel):
    """Typed entity identifier."""

    value: str = Field(min_length=1)


def generate_entity_id(*, prefix: str = "entity") -> str:
    """Generate a unique entity identifier."""
    normalized_prefix = prefix.strip().lower().replace(" ", "-")
    if not normalized_prefix:
        msg = "Identifier prefix must not be empty"
        raise IdentifierError(msg)
    return f"{normalized_prefix}-{uuid4()}"


def validate_entity_id(value: str) -> str:
    """Validate and normalize an entity identifier."""
    normalized = value.strip().lower()
    if not normalized:
        msg = "Entity identifier must not be empty"
        raise IdentifierError(msg)
    if not _ID_PATTERN.match(normalized):
        msg = (
            "Entity identifier must start with a letter and contain only "
            "lowercase letters, digits, underscores, or hyphens"
        )
        raise IdentifierError(msg)
    return normalized


class IdManager:
    """Tracks issued entity identifiers within a runtime scope."""

    def __init__(self) -> None:
        self._issued: set[str] = set()

    def issue(self, *, prefix: str = "entity") -> EntityId:
        """Issue a unique entity identifier."""
        for _ in range(8):
            candidate = generate_entity_id(prefix=prefix)
            if candidate not in self._issued:
                self._issued.add(candidate)
                return EntityId(value=candidate)
        msg = "Failed to issue a unique entity identifier"
        raise IdentifierError(msg)

    def register(self, entity_id: str) -> EntityId:
        """Register an externally supplied entity identifier."""
        normalized = validate_entity_id(entity_id)
        if normalized in self._issued:
            msg = f"Entity identifier already issued: {normalized}"
            raise IdentifierError(msg)
        self._issued.add(normalized)
        return EntityId(value=normalized)

    def exists(self, entity_id: str) -> bool:
        return validate_entity_id(entity_id) in self._issued

    def list(self) -> tuple[str, ...]:
        return tuple(sorted(self._issued))
