"""Helpers for Decision layer tests."""

from __future__ import annotations

from typing import Any

from decision.engine.decision_context import DecisionContext
from decision.engine.decision_engine import DecisionEngine, DecisionEngineMetadata
from decision.engine.decision_result import DecisionResult
from decision.engine.decision_state import DecisionState
from decision.policy.decision_policy import DecisionPolicy, PolicyMetadata
from decision.policy.policy_result import PolicyResult


def make_engine_metadata(
    *,
    engine_id: str = "sample-engine",
    name: str = "Sample Engine",
    version: str = "1.0.0",
) -> DecisionEngineMetadata:
    return DecisionEngineMetadata(
        engine_id=engine_id,
        name=name,
        version=version,
        capabilities=("evaluation",),
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


class SampleDecisionEngine(DecisionEngine):
    """Concrete decision engine used in unit tests."""

    def engine_id(self) -> str:
        return "sample-engine"

    def name(self) -> str:
        return "Sample Engine"

    def version(self) -> str:
        return "1.0.0"

    def process(self, context: DecisionContext) -> DecisionResult:
        return DecisionResult(
            decision_id=context.decision_id,
            engine_id=self.engine_id(),
            state=DecisionState.PROCESSING,
            output={"decision_id": context.decision_id},
            metadata={"engine": self.name()},
            confidence=0.85,
            version_info={"engine_version": self.version()},
        )


class FailingDecisionEngine(DecisionEngine):
    """Decision engine that fails during processing."""

    def engine_id(self) -> str:
        return "failing-engine"

    def name(self) -> str:
        return "Failing Engine"

    def version(self) -> str:
        return "1.0.0"

    def process(self, context: DecisionContext) -> DecisionResult:
        raise RuntimeError("decision processing failed")


class SamplePolicy(DecisionPolicy):
    """Concrete decision policy used in unit tests."""

    def policy_id(self) -> str:
        return "sample-policy"

    def name(self) -> str:
        return "Sample Policy"

    def version(self) -> str:
        return "1.0.0"

    def evaluate(
        self,
        context: DecisionContext,
        *,
        ai_output: dict[str, Any],
        ml_output: dict[str, Any],
    ) -> PolicyResult:
        combined = {**ai_output, **ml_output}
        return PolicyResult(
            policy_id=self.policy_id(),
            accepted=True,
            output={"policy_evaluated": True, "fields": float(len(combined))},
            metadata={"policy": self.name()},
            confidence=0.9,
            version=self.version(),
        )


class RejectingPolicy(DecisionPolicy):
    """Policy that rejects all inputs."""

    def policy_id(self) -> str:
        return "rejecting-policy"

    def name(self) -> str:
        return "Rejecting Policy"

    def version(self) -> str:
        return "1.0.0"

    def evaluate(
        self,
        context: DecisionContext,
        *,
        ai_output: dict[str, Any],
        ml_output: dict[str, Any],
    ) -> PolicyResult:
        return PolicyResult(
            policy_id=self.policy_id(),
            accepted=False,
            output={"rejected": True},
            metadata={"policy": self.name()},
            confidence=0.0,
            version=self.version(),
        )
