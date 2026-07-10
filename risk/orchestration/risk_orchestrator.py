"""Risk orchestrator."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from core.context.core_context import CoreContext
from decision.engine.decision_result import DecisionResult
from risk.engine.risk_context import RiskContext
from risk.engine.risk_engine import RiskEngine
from risk.engine.risk_result import RiskResult
from risk.engine.risk_state import RiskState
from risk.exceptions import OrchestrationError, PolicyNotFoundError, RiskNotFoundError
from risk.policy.policy_registry import PolicyRegistry
from risk.policy.risk_policy import RiskPolicy
from risk.registry.risk_registry import RiskRegistry
from risk.scoring.approval_score import ApprovalScore
from risk.scoring.confidence_score import ConfidenceScore
from risk.scoring.scoring_engine import ScoringEngine
from risk.validation.validation_result import ValidationResult
from risk.validation.validator import Validator


class RiskOrchestrator:
    """Coordinates risk assessment: validation -> policy -> scoring -> result."""

    def __init__(
        self,
        *,
        engine_registry: RiskRegistry | None = None,
        policy_registry: PolicyRegistry | None = None,
        validator: Validator | None = None,
        scoring_engine: ScoringEngine | None = None,
    ) -> None:
        self._engines = engine_registry or RiskRegistry()
        self._policies = policy_registry or PolicyRegistry()
        self._validator = validator or Validator()
        self._scoring = scoring_engine or ScoringEngine()

    def create_context(
        self,
        *,
        core_context: CoreContext | None = None,
        decision_result: DecisionResult | None = None,
        input_data: dict[str, Any] | None = None,
    ) -> RiskContext:
        risk_id = str(uuid4())
        correlation_id = core_context.correlation_id if core_context else str(uuid4())
        trace_id = core_context.trace_id if core_context else str(uuid4())
        return RiskContext(
            risk_id=risk_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            core_context=core_context,
            decision_result=decision_result,
            input_data=input_data or {},
        )

    def assess(
        self,
        context: RiskContext,
        engine: RiskEngine,
        *,
        policy_id: str,
        policy: RiskPolicy | None = None,
    ) -> RiskResult:
        """Execute the risk pipeline: validation -> policy -> scoring -> result."""
        engine_id = engine.engine_id()
        if not self._engines.exists(engine_id):
            raise RiskNotFoundError(engine_id)
        if not self._policies.exists(policy_id):
            raise PolicyNotFoundError(policy_id)

        self._engines.set_state(engine_id, RiskState.PROCESSING)
        try:
            validation_result = self._validator.validate(context)
            if not validation_result.passed:
                self._engines.set_state(engine_id, RiskState.REJECTED)
                return self._build_rejected_result(
                    context=context,
                    engine_id=engine_id,
                    policy_id=policy_id,
                    validation_result=validation_result,
                    reason="validation_failed",
                )

            engine_result = engine.assess(context)
            decision_output = self._extract_decision_output(context)
            policy_impl = policy or self._policies.resolve_type(policy_id)()
            policy_result = policy_impl.evaluate(
                context,
                validation_result=validation_result,
                decision_output=decision_output,
            )

            if not policy_result.compliant:
                self._engines.set_state(engine_id, RiskState.REJECTED)
                return self._build_rejected_result(
                    context=context,
                    engine_id=engine_id,
                    policy_id=policy_id,
                    validation_result=validation_result,
                    reason="policy_non_compliant",
                    policy_output=policy_result.output,
                )

            confidence, approval = self._scoring.score(
                validation_result=validation_result,
                policy_result=policy_result,
                engine_result=engine_result,
            )
            merged = self._merge_result(
                context=context,
                engine_result=engine_result,
                policy_id=policy_id,
                validation_result=validation_result,
                confidence=confidence,
                approval=approval,
                policy_version=policy_result.version,
            )
            self._engines.set_state(engine_id, RiskState.APPROVED)
            return merged
        except RiskNotFoundError, PolicyNotFoundError:
            raise
        except Exception as error:
            self._engines.set_state(engine_id, RiskState.FAILED)
            msg = f"Risk orchestration failed: {error}"
            raise OrchestrationError(msg) from error

    def _extract_decision_output(self, context: RiskContext) -> dict[str, Any]:
        if context.decision_result is None:
            return {}
        return dict(context.decision_result.output)

    def _build_rejected_result(
        self,
        *,
        context: RiskContext,
        engine_id: str,
        policy_id: str,
        validation_result: ValidationResult,
        reason: str,
        policy_output: dict[str, Any] | None = None,
    ) -> RiskResult:
        return RiskResult(
            risk_id=context.risk_id,
            engine_id=engine_id,
            policy_id=policy_id,
            state=RiskState.REJECTED,
            output=policy_output or {"rejected": True, "reason": reason},
            metadata={"reason": reason},
            validation={
                "validation_id": validation_result.validation_id,
                "passed": validation_result.passed,
                "failed_rules": list(validation_result.failed_rules),
            },
        )

    def _merge_result(
        self,
        *,
        context: RiskContext,
        engine_result: RiskResult,
        policy_id: str,
        validation_result: ValidationResult,
        confidence: ConfidenceScore,
        approval: ApprovalScore,
        policy_version: str,
    ) -> RiskResult:
        return RiskResult(
            risk_id=context.risk_id,
            engine_id=engine_result.engine_id,
            policy_id=policy_id,
            state=RiskState.APPROVED,
            output=engine_result.output,
            metadata=engine_result.metadata,
            confidence=confidence,
            approval=approval,
            validation={
                "validation_id": validation_result.validation_id,
                "passed": validation_result.passed,
                "passed_rules": list(validation_result.passed_rules),
            },
            version_info={
                "engine_version": engine_result.version_info.get("engine_version", ""),
                "policy_version": policy_version,
            },
        )
