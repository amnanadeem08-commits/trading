"""Decision orchestrator."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from ai.evaluation.ai_evaluation_result import AIEvaluationResult
from ai.reasoning.reasoning_result import ReasoningResult
from core.context.core_context import CoreContext
from decision.engine.decision_context import DecisionContext
from decision.engine.decision_engine import DecisionEngine
from decision.engine.decision_result import DecisionResult
from decision.engine.decision_state import DecisionState
from decision.evaluation.decision_evaluator import DecisionEvaluator, InMemoryDecisionEvaluator
from decision.evaluation.decision_metrics import DecisionMetrics
from decision.exceptions import DecisionNotFoundError, OrchestrationError, PolicyNotFoundError
from decision.policy.decision_policy import DecisionPolicy
from decision.policy.policy_registry import PolicyRegistry
from decision.policy.policy_result import PolicyResult
from decision.registry.decision_registry import DecisionRegistry
from ml.evaluation.evaluation_result import EvaluationResult
from ml.inference.prediction_result import PredictionResult


class DecisionOrchestrator:
    """Coordinates decision processing across engines, policies, and evaluation."""

    def __init__(
        self,
        *,
        engine_registry: DecisionRegistry | None = None,
        policy_registry: PolicyRegistry | None = None,
        evaluator: DecisionEvaluator | None = None,
    ) -> None:
        self._engines = engine_registry or DecisionRegistry()
        self._policies = policy_registry or PolicyRegistry()
        self._evaluator = evaluator or InMemoryDecisionEvaluator()

    def create_context(
        self,
        *,
        core_context: CoreContext | None = None,
        ai_result: ReasoningResult | None = None,
        ml_result: PredictionResult | None = None,
        ml_evaluation: EvaluationResult | None = None,
        ai_evaluation: AIEvaluationResult | None = None,
        input_data: dict[str, Any] | None = None,
    ) -> DecisionContext:
        decision_id = str(uuid4())
        correlation_id = core_context.correlation_id if core_context else str(uuid4())
        trace_id = core_context.trace_id if core_context else str(uuid4())
        return DecisionContext(
            decision_id=decision_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            core_context=core_context,
            ai_result=ai_result,
            ml_result=ml_result,
            ml_evaluation=ml_evaluation,
            ai_evaluation=ai_evaluation,
            input_data=input_data or {},
        )

    def decide(
        self,
        context: DecisionContext,
        engine: DecisionEngine,
        *,
        policy_id: str,
        policy: DecisionPolicy | None = None,
    ) -> DecisionResult:
        """Execute the decision pipeline: engine -> policy -> evaluation."""
        engine_id = engine.engine_id()
        if not self._engines.exists(engine_id):
            raise DecisionNotFoundError(engine_id)
        if not self._policies.exists(policy_id):
            raise PolicyNotFoundError(policy_id)

        self._engines.set_state(engine_id, DecisionState.PROCESSING)
        try:
            engine_result = engine.process(context)
            ai_output = self._extract_ai_output(context)
            ml_output = self._extract_ml_output(context)
            policy_impl = policy or self._policies.resolve_type(policy_id)()
            policy_result = policy_impl.evaluate(
                context,
                ai_output=ai_output,
                ml_output=ml_output,
            )

            if not policy_result.accepted:
                self._engines.set_state(engine_id, DecisionState.REJECTED)
                return DecisionResult(
                    decision_id=context.decision_id,
                    engine_id=engine_id,
                    policy_id=policy_id,
                    state=DecisionState.REJECTED,
                    output=policy_result.output,
                    metadata={
                        **engine_result.metadata,
                        **policy_result.metadata,
                    },
                    confidence=policy_result.confidence,
                    version_info={"policy_version": policy_result.version},
                )

            metrics = self._evaluator.evaluate(
                decision_id=context.decision_id,
                result=engine_result,
            )
            merged = self._merge_result(
                context=context,
                engine_result=engine_result,
                policy_result=policy_result,
                policy_id=policy_id,
                metrics=metrics,
            )
            self._engines.set_state(engine_id, DecisionState.COMPLETED)
            return merged
        except DecisionNotFoundError, PolicyNotFoundError:
            raise
        except Exception as error:
            self._engines.set_state(engine_id, DecisionState.FAILED)
            msg = f"Decision orchestration failed: {error}"
            raise OrchestrationError(msg) from error

    def _extract_ai_output(self, context: DecisionContext) -> dict[str, Any]:
        if context.ai_result is None:
            return {}
        return dict(context.ai_result.output)

    def _extract_ml_output(self, context: DecisionContext) -> dict[str, Any]:
        if context.ml_result is None or not context.ml_result.outputs:
            return {}
        return dict(context.ml_result.outputs[0])

    def _merge_result(
        self,
        *,
        context: DecisionContext,
        engine_result: DecisionResult,
        policy_result: PolicyResult,
        policy_id: str,
        metrics: DecisionMetrics,
    ) -> DecisionResult:
        confidence = max(engine_result.confidence, policy_result.confidence)
        return DecisionResult(
            decision_id=context.decision_id,
            engine_id=engine_result.engine_id,
            policy_id=policy_id,
            state=DecisionState.COMPLETED,
            output={**engine_result.output, **policy_result.output},
            metadata={**engine_result.metadata, **policy_result.metadata},
            confidence=confidence,
            evaluation={
                "quality_score": metrics.quality_score,
                "consistency_score": metrics.consistency_score,
                "confidence": confidence,
                "details": metrics.details,
            },
            version_info={
                "engine_version": engine_result.version_info.get("engine_version", ""),
                "policy_version": policy_result.version,
            },
        )
