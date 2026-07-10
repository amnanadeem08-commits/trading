"""Helpers for Risk layer tests."""

from __future__ import annotations

from typing import Any

from decision.engine.decision_result import DecisionResult
from decision.engine.decision_state import DecisionState
from risk.engine.risk_context import RiskContext
from risk.engine.risk_engine import RiskEngine, RiskEngineMetadata
from risk.engine.risk_result import RiskResult
from risk.engine.risk_state import RiskState
from risk.policy.policy_result import PolicyResult
from risk.policy.risk_policy import PolicyMetadata, RiskPolicy
from risk.scoring.confidence_score import ConfidenceScore
from risk.validation.validation_result import ValidationResult
from risk.validation.validation_rule import ValidationRule


def make_engine_metadata(
    *,
    engine_id: str = "sample-engine",
    name: str = "Sample Engine",
    version: str = "1.0.0",
) -> RiskEngineMetadata:
    return RiskEngineMetadata(
        engine_id=engine_id,
        name=name,
        version=version,
        capabilities=("assessment",),
        tags=("test",),
    )


def make_policy_metadata(
    *,
    policy_id: str = "sample-policy",
    name: str = "Sample Policy",
    version: str = "1.0.0",
) -> PolicyMetadata:
    return PolicyMetadata(
        policy_id=policy_id,
        name=name,
        version=version,
        tags=("test",),
    )


def make_decision_result(
    *,
    decision_id: str = "dec-1",
    confidence: float = 0.85,
) -> DecisionResult:
    return DecisionResult(
        decision_id=decision_id,
        engine_id="decision-engine",
        state=DecisionState.COMPLETED,
        output={"outcome": "approved", "confidence": confidence},
        confidence=confidence,
    )


class SampleRiskEngine(RiskEngine):
    """Concrete risk engine used in unit tests."""

    def engine_id(self) -> str:
        return "sample-engine"

    def name(self) -> str:
        return "Sample Engine"

    def version(self) -> str:
        return "1.0.0"

    def assess(self, context: RiskContext) -> RiskResult:
        return RiskResult(
            risk_id=context.risk_id,
            engine_id=self.engine_id(),
            state=RiskState.PROCESSING,
            output={"risk_id": context.risk_id},
            metadata={"engine": self.name()},
            confidence=ConfidenceScore(value=0.85, source="engine"),
            version_info={"engine_version": self.version()},
        )


class FailingRiskEngine(RiskEngine):
    """Risk engine that fails during assessment."""

    def engine_id(self) -> str:
        return "failing-engine"

    def name(self) -> str:
        return "Failing Engine"

    def version(self) -> str:
        return "1.0.0"

    def assess(self, context: RiskContext) -> RiskResult:
        raise RuntimeError("risk assessment failed")


class SamplePolicy(RiskPolicy):
    """Concrete risk policy used in unit tests."""

    def policy_id(self) -> str:
        return "sample-policy"

    def name(self) -> str:
        return "Sample Policy"

    def version(self) -> str:
        return "1.0.0"

    def evaluate(
        self,
        context: RiskContext,
        *,
        validation_result: ValidationResult,
        decision_output: dict[str, Any],
    ) -> PolicyResult:
        return PolicyResult(
            policy_id=self.policy_id(),
            compliant=True,
            output={"policy_evaluated": True, "fields": float(len(decision_output))},
            metadata={"policy": self.name()},
            score=0.9,
            version=self.version(),
        )


class RejectingPolicy(RiskPolicy):
    """Policy that rejects all inputs."""

    def policy_id(self) -> str:
        return "rejecting-policy"

    def name(self) -> str:
        return "Rejecting Policy"

    def version(self) -> str:
        return "1.0.0"

    def evaluate(
        self,
        context: RiskContext,
        *,
        validation_result: ValidationResult,
        decision_output: dict[str, Any],
    ) -> PolicyResult:
        return PolicyResult(
            policy_id=self.policy_id(),
            compliant=False,
            output={"rejected": True},
            metadata={"policy": self.name()},
            score=0.0,
            version=self.version(),
        )


class PassingRule(ValidationRule):
    """Validation rule that always passes."""

    def rule_id(self) -> str:
        return "passing-rule"

    def name(self) -> str:
        return "Passing Rule"

    def validate(self, context: RiskContext, *, input_data: dict[str, Any]) -> bool:
        return True


class FailingRule(ValidationRule):
    """Validation rule that always fails."""

    def rule_id(self) -> str:
        return "failing-rule"

    def name(self) -> str:
        return "Failing Rule"

    def validate(self, context: RiskContext, *, input_data: dict[str, Any]) -> bool:
        return False
