"""Agent domain contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import Field

from ai.agents.agent_context import AgentContext
from ai.agents.agent_lifecycle import AgentState
from ai.reasoning.reasoning_result import ReasoningResult
from models.common import PlatformModel


class AgentMetadata(PlatformModel):
    """Metadata describing a registered AI agent."""

    agent_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    capabilities: tuple[str, ...] = Field(default_factory=tuple)
    tags: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)


class Agent(ABC):
    """Executable AI agent implementation contract."""

    @abstractmethod
    def agent_id(self) -> str:
        """Return the agent identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the agent display name."""

    @abstractmethod
    def version(self) -> str:
        """Return the agent version."""

    def metadata(self) -> AgentMetadata:
        """Return agent metadata."""
        return AgentMetadata(
            agent_id=self.agent_id(),
            name=self.name(),
            version=self.version(),
        )

    def capabilities(self) -> tuple[str, ...]:
        """Return agent capability identifiers."""
        return ()

    @abstractmethod
    def execute(self, context: AgentContext) -> ReasoningResult:
        """Execute the agent with the provided context."""

    def initialize(self, context: AgentContext) -> AgentContext:
        """Initialize the agent for execution. Default is identity."""
        return context

    def to_definition(self, *, state: AgentState = AgentState.CREATED) -> AgentMetadata:
        """Convert the agent implementation to a registered definition."""
        return self.metadata().model_copy(update={"attributes": {"state": state.value}})
