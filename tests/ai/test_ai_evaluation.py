"""Unit tests for AI evaluation framework."""

from __future__ import annotations

import pytest

from ai import AIEvaluationState, InMemoryAIEvaluator
from ai.reasoning.reasoning_result import ReasoningResult


@pytest.mark.unit
def test_in_memory_ai_evaluator() -> None:
    evaluator = InMemoryAIEvaluator()
    result = ReasoningResult(
        reasoning_id="reason-1",
        agent_id="sample-agent",
        output={"answer": "yes"},
        confidence=0.85,
    )
    evaluation = evaluator.evaluate(
        agent_id="sample-agent",
        task_id="task-1",
        result=result,
    )
    assert evaluation.state == AIEvaluationState.COMPLETED
    assert evaluation.quality_score == 0.85
    assert evaluation.metrics["confidence"] == 0.85
