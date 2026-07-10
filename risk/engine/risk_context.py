"""Risk context contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ai.reasoning.reasoning_result import ReasoningResult
from core.context.core_context import CoreContext
from decision.engine.decision_result import DecisionResult
from models.common import PlatformModel


class RiskContext(PlatformModel):
    """Input context for risk engine, validation, and policy evaluation."""

    risk_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    core_context: CoreContext | None = None
    decision_result: DecisionResult | None = None
    ai_result: ReasoningResult | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
