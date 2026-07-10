"""Execution context contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from core.context.core_context import CoreContext
from decision.engine.decision_result import DecisionResult
from models.common import PlatformModel
from risk.engine.risk_result import RiskResult


class ExecutionContext(PlatformModel):
    """Input context for execution engine and dispatch operations."""

    execution_id: str = Field(min_length=1)
    correlation_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    core_context: CoreContext | None = None
    risk_result: RiskResult | None = None
    decision_result: DecisionResult | None = None
    input_data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
