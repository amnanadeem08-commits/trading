"""Helpers for AI layer tests."""

from __future__ import annotations

from ai.agents.agent import Agent, AgentMetadata
from ai.agents.agent_context import AgentContext
from ai.reasoning.reasoning_result import ReasoningResult


def make_agent_metadata(
    *,
    agent_id: str = "sample-agent",
    name: str = "Sample Agent",
    version: str = "1.0.0",
) -> AgentMetadata:
    return AgentMetadata(
        agent_id=agent_id,
        name=name,
        version=version,
        capabilities=("reasoning",),
        tags=("test",),
    )


class SampleAgent(Agent):
    """Concrete AI agent used in unit tests."""

    def agent_id(self) -> str:
        return "sample-agent"

    def name(self) -> str:
        return "Sample Agent"

    def version(self) -> str:
        return "1.0.0"

    def capabilities(self) -> tuple[str, ...]:
        return ("reasoning",)

    def execute(self, context: AgentContext) -> ReasoningResult:
        return ReasoningResult(
            reasoning_id=f"reasoning-{context.task_id}",
            agent_id=self.agent_id(),
            output={"task_id": context.task_id},
            metadata={"agent": self.name()},
            confidence=0.9,
        )


class FailingAgent(Agent):
    """Agent that fails during execution."""

    def agent_id(self) -> str:
        return "failing-agent"

    def name(self) -> str:
        return "Failing Agent"

    def version(self) -> str:
        return "1.0.0"

    def execute(self, context: AgentContext) -> ReasoningResult:
        raise RuntimeError("agent execution failed")
