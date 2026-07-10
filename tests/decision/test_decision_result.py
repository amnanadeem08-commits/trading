"""Unit tests for decision result."""

from __future__ import annotations

from decision import DecisionResult, DecisionState


def test_decision_result_defaults() -> None:
    result = DecisionResult(
        decision_id="dec-1",
        engine_id="engine-1",
    )
    assert result.state == DecisionState.COMPLETED
    assert result.confidence == 0.0
    assert result.output == {}
    assert result.evaluation == {}
    assert result.version_info == {}


def test_decision_result_full() -> None:
    result = DecisionResult(
        decision_id="dec-1",
        engine_id="engine-1",
        policy_id="policy-1",
        state=DecisionState.COMPLETED,
        output={"outcome": "approved"},
        metadata={"engine": "sample"},
        confidence=0.95,
        evaluation={"quality_score": 0.95, "consistency_score": 1.0},
        version_info={"engine_version": "1.0.0", "policy_version": "1.0.0"},
    )
    assert result.policy_id == "policy-1"
    assert result.evaluation["quality_score"] == 0.95
    assert result.version_info["policy_version"] == "1.0.0"
