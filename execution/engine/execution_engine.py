"""Execution engine contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import Field

from execution.engine.execution_context import ExecutionContext
from execution.engine.execution_result import ExecutionResult
from models.common import PlatformModel


class ExecutionEngineMetadata(PlatformModel):
    """Metadata for a registered execution engine."""

    engine_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)


class ExecutionEngine(ABC):
    """Generic execution engine contract."""

    @abstractmethod
    def engine_id(self) -> str:
        """Return the unique engine identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the human-readable engine name."""

    @abstractmethod
    def version(self) -> str:
        """Return the engine version."""

    def metadata(self) -> ExecutionEngineMetadata:
        """Return engine metadata."""
        return ExecutionEngineMetadata(
            engine_id=self.engine_id(),
            name=self.name(),
            version=self.version(),
        )

    @abstractmethod
    def execute(self, context: ExecutionContext) -> ExecutionResult:
        """Prepare an execution contract from the given context."""
