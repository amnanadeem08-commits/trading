"""Risk result contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from risk.engine.risk_state import RiskState
from risk.scoring.approval_score import ApprovalScore
from risk.scoring.confidence_score import ConfidenceScore


class RiskResult(PlatformModel):
    """Outcome of a risk assessment operation."""

    risk_id: str = Field(min_length=1)
    engine_id: str = Field(min_length=1)
    policy_id: str = ""
    state: RiskState = RiskState.APPROVED
    output: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    confidence: ConfidenceScore | None = None
    approval: ApprovalScore | None = None
    validation: dict[str, Any] = Field(default_factory=dict)
    version_info: dict[str, str] = Field(default_factory=dict)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
