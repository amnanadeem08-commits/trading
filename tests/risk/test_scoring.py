"""Unit tests for scoring framework."""

from __future__ import annotations

from risk import RiskResult, RiskState
from risk.policy.policy_result import PolicyResult
from risk.scoring.approval_score import ApprovalScore
from risk.scoring.confidence_score import ConfidenceScore
from risk.scoring.scoring_engine import ScoringEngine
from risk.validation.validation_result import ValidationResult, ValidationState


def test_confidence_score_fields() -> None:
    score = ConfidenceScore(value=0.9, source="test", metadata={"key": "val"})
    assert score.value == 0.9
    assert score.source == "test"


def test_approval_score_fields() -> None:
    score = ApprovalScore(value=0.8, approved=True)
    assert score.approved is True
    assert score.value == 0.8


def test_scoring_engine_approved() -> None:
    engine = ScoringEngine()
    validation = ValidationResult(validation_id="val-1", state=ValidationState.PASSED)
    policy = PolicyResult(policy_id="pol-1", compliant=True, score=0.9)
    risk_result = RiskResult(
        risk_id="risk-1",
        engine_id="engine-1",
        state=RiskState.PROCESSING,
        confidence=ConfidenceScore(value=0.85, source="engine"),
    )
    confidence, approval = engine.score(
        validation_result=validation,
        policy_result=policy,
        engine_result=risk_result,
    )
    assert confidence.value >= 0.85
    assert approval.approved is True
    assert approval.value > 0.0


def test_scoring_engine_validation_failed() -> None:
    engine = ScoringEngine()
    validation = ValidationResult(
        validation_id="val-1",
        state=ValidationState.FAILED,
        failed_rules=("rule-1",),
    )
    policy = PolicyResult(policy_id="pol-1", compliant=True, score=0.9)
    risk_result = RiskResult(risk_id="risk-1", engine_id="engine-1")
    _confidence, approval = engine.score(
        validation_result=validation,
        policy_result=policy,
        engine_result=risk_result,
    )
    assert approval.approved is False
    assert approval.value == 0.0
