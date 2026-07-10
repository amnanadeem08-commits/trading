"""AI evaluator interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import uuid4

from ai.evaluation.ai_evaluation_result import AIEvaluationResult, AIEvaluationState
from ai.reasoning.reasoning_result import ReasoningResult


class AIEvaluator(ABC):
    """Coordinates AI output evaluation."""

    @abstractmethod
    def evaluate(
        self,
        *,
        agent_id: str,
        task_id: str,
        result: ReasoningResult,
    ) -> AIEvaluationResult:
        """Evaluate an AI reasoning result."""


class InMemoryAIEvaluator(AIEvaluator):
    """In-memory AI evaluator for platform scaffolding."""

    def evaluate(
        self,
        *,
        agent_id: str,
        task_id: str,
        result: ReasoningResult,
    ) -> AIEvaluationResult:
        evaluation_id = str(uuid4())
        quality_score = result.confidence
        metrics = {
            "confidence": result.confidence,
            "output_fields": float(len(result.output)),
        }
        return AIEvaluationResult(
            evaluation_id=evaluation_id,
            agent_id=agent_id,
            task_id=task_id,
            state=AIEvaluationState.COMPLETED,
            quality_score=quality_score,
            metrics=metrics,
            metadata={"evaluator": "in_memory"},
        )
