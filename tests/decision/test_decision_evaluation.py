"""Unit tests for decision evaluation."""

from __future__ import annotations

from decision import DecisionResult, DecisionState, InMemoryDecisionEvaluator
from decision.evaluation.decision_metrics import DecisionMetrics


def test_decision_metrics_fields() -> None:
    metrics = DecisionMetrics(
        quality_score=0.9,
        consistency_score=1.0,
        metadata={"evaluator": "test"},
        details={"confidence": 0.9},
    )
    assert metrics.quality_score == 0.9
    assert metrics.consistency_score == 1.0


def test_in_memory_evaluator_completed() -> None:
    evaluator = InMemoryDecisionEvaluator()
    result = DecisionResult(
        decision_id="dec-1",
        engine_id="engine-1",
        state=DecisionState.COMPLETED,
        confidence=0.85,
        output={"outcome": "approved"},
        evaluation={"confidence": 0.85},
    )
    metrics = evaluator.evaluate(decision_id="dec-1", result=result)
    assert metrics.quality_score == 0.85
    assert metrics.consistency_score == 1.0
    assert metrics.details["confidence"] == 0.85


def test_in_memory_evaluator_rejected() -> None:
    evaluator = InMemoryDecisionEvaluator()
    result = DecisionResult(
        decision_id="dec-1",
        engine_id="engine-1",
        state=DecisionState.REJECTED,
        confidence=0.0,
    )
    metrics = evaluator.evaluate(decision_id="dec-1", result=result)
    assert metrics.consistency_score == 0.5
