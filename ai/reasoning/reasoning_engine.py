"""Reasoning engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ai.reasoning.reasoning_context import ReasoningContext
from ai.reasoning.reasoning_result import ReasoningResult


class ReasoningEngine(ABC):
    """Coordinates reasoning operations for AI agents."""

    @abstractmethod
    def reason(self, context: ReasoningContext) -> ReasoningResult:
        """Execute reasoning with the provided context."""


class PassthroughReasoningEngine(ReasoningEngine):
    """Passthrough reasoning engine for platform scaffolding."""

    def reason(self, context: ReasoningContext) -> ReasoningResult:
        return ReasoningResult(
            reasoning_id=context.reasoning_id,
            agent_id=context.agent_context.agent_id,
            output=dict(context.input_data),
            metadata={"engine": "passthrough"},
            confidence=1.0,
        )
