"""Scoring engine."""

from __future__ import annotations

from risk.engine.risk_result import RiskResult
from risk.policy.policy_result import PolicyResult
from risk.scoring.approval_score import ApprovalScore
from risk.scoring.confidence_score import ConfidenceScore
from risk.validation.validation_result import ValidationResult


class ScoringEngine:
    """Computes generic confidence and approval scores from assessment inputs."""

    def score(
        self,
        *,
        validation_result: ValidationResult,
        policy_result: PolicyResult,
        engine_result: RiskResult,
    ) -> tuple[ConfidenceScore, ApprovalScore]:
        """Compute confidence and approval scores."""
        base_confidence = policy_result.score
        if engine_result.confidence is not None:
            base_confidence = max(base_confidence, engine_result.confidence.value)

        validation_factor = 1.0 if validation_result.passed else 0.5
        confidence_value = min(base_confidence * validation_factor, 1.0)

        approved = policy_result.compliant and validation_result.passed
        approval_value = confidence_value if approved else 0.0

        confidence = ConfidenceScore(
            value=confidence_value,
            source="scoring_engine",
            metadata={
                "validation_passed": str(validation_result.passed),
                "policy_compliant": str(policy_result.compliant),
            },
        )
        approval = ApprovalScore(
            value=approval_value,
            approved=approved,
            metadata={"engine_id": engine_result.engine_id},
        )
        return confidence, approval
