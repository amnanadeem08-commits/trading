"""Core entity contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import Field

from core.state.operation_state import OperationState
from models.common import PlatformModel


class Entity(PlatformModel):
    """Registered platform entity definition."""

    entity_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    state: OperationState = OperationState.REGISTERED
    dependencies: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)


class BaseEntity(ABC):
    """Executable entity implementation contract."""

    @abstractmethod
    def entity_id(self) -> str:
        """Return the entity identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the entity display name."""

    @abstractmethod
    def version(self) -> str:
        """Return the entity version."""

    @abstractmethod
    def entity_type(self) -> str:
        """Return the entity type identifier."""

    def dependencies(self) -> tuple[str, ...]:
        """Return entity identifiers this entity depends on."""
        return ()

    def metadata(self) -> dict[str, str]:
        """Return entity metadata."""
        return {}

    def to_definition(self, *, state: OperationState = OperationState.REGISTERED) -> Entity:
        """Convert the entity implementation to a registered definition."""
        return Entity(
            entity_id=self.entity_id(),
            name=self.name(),
            version=self.version(),
            entity_type=self.entity_type(),
            state=state,
            dependencies=self.dependencies(),
            metadata=self.metadata(),
        )
