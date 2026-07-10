"""Risk engine contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import Field

from models.common import PlatformModel
from risk.engine.risk_context import RiskContext
from risk.engine.risk_result import RiskResult


class RiskEngineMetadata(PlatformModel):
    """Metadata for a registered risk engine."""

    engine_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)


class RiskEngine(ABC):
    """Generic risk engine contract."""

    @abstractmethod
    def engine_id(self) -> str:
        """Return the unique engine identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the human-readable engine name."""

    @abstractmethod
    def version(self) -> str:
        """Return the engine version."""

    def metadata(self) -> RiskEngineMetadata:
        """Return engine metadata."""
        return RiskEngineMetadata(
            engine_id=self.engine_id(),
            name=self.name(),
            version=self.version(),
        )

    @abstractmethod
    def assess(self, context: RiskContext) -> RiskResult:
        """Assess risk for a given context and return a result."""
