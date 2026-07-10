"""Decision evaluator interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from decision.engine.decision_result import DecisionResult
from decision.evaluation.decision_metrics import DecisionMetrics


class DecisionEvaluator(ABC):
    """Coordinates decision output evaluation."""

    @abstractmethod
    def evaluate(self, *, decision_id: str, result: DecisionResult) -> DecisionMetrics:
        """Evaluate a decision result for quality and consistency."""


class InMemoryDecisionEvaluator(DecisionEvaluator):
    """In-memory decision evaluator for platform scaffolding."""

    def evaluate(self, *, decision_id: str, result: DecisionResult) -> DecisionMetrics:
        quality_score = result.confidence
        consistency_score = 1.0 if result.state.value == "completed" else 0.5
        details: dict[str, float] = {
            "confidence": result.confidence,
            "output_fields": float(len(result.output)),
        }
        evaluation_confidence = result.evaluation.get("confidence")
        if isinstance(evaluation_confidence, (int, float)):
            details["evaluation_confidence"] = float(evaluation_confidence)
        return DecisionMetrics(
            quality_score=quality_score,
            consistency_score=consistency_score,
            metadata={"evaluator": "in_memory", "decision_id": decision_id},
            details=details,
        )
