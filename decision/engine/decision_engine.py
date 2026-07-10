"""Decision engine contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import Field

from decision.engine.decision_context import DecisionContext
from decision.engine.decision_result import DecisionResult
from models.common import PlatformModel


class DecisionEngineMetadata(PlatformModel):
    """Metadata for a registered decision engine."""

    engine_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)


class DecisionEngine(ABC):
    """Generic decision engine contract."""

    @abstractmethod
    def engine_id(self) -> str:
        """Return the unique engine identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the human-readable engine name."""

    @abstractmethod
    def version(self) -> str:
        """Return the engine version."""

    def metadata(self) -> DecisionEngineMetadata:
        """Return engine metadata."""
        return DecisionEngineMetadata(
            engine_id=self.engine_id(),
            name=self.name(),
            version=self.version(),
        )

    @abstractmethod
    def process(self, context: DecisionContext) -> DecisionResult:
        """Process a decision context and return a result."""
