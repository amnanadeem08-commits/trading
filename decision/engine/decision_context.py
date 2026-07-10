"""Decision context contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.evaluation.ai_evaluation_result import AIEvaluationResult
from ai.reasoning.reasoning_result import ReasoningResult
from core.context.core_context import CoreContext
from ml.evaluation.evaluation_result import EvaluationResult
from ml.inference.prediction_result import PredictionResult
from models.common import PlatformModel


class DecisionContext(PlatformModel):
    """Input context for decision engine and policy evaluation."""

    decision_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    core_context: CoreContext | None = None
    ai_result: ReasoningResult | None = None
    ml_result: PredictionResult | None = None
    ml_evaluation: EvaluationResult | None = None
    ai_evaluation: AIEvaluationResult | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
