"""Risk engine contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from models.decision import TradingDecision


class RiskVerdictStatus(StrEnum):
    """Risk engine verdict."""

    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class RiskAssessment(PlatformModel):
    """Risk narrative attached to explainability bundle."""

    exposure_impact: str = Field(min_length=1)
    margin_impact: str | None = None
    daily_loss_remaining_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    position_limit_remaining_pct: float | None = Field(default=None, ge=0.0, le=1.0)
    notes: str | None = None


class RiskVerdict(PlatformModel):
    """Output of the Risk Engine. Gates execution."""

    verdict_id: str = Field(min_length=1)
    decision: TradingDecision
    status: RiskVerdictStatus
    modified_decision: TradingDecision | None = None
    assessment: RiskAssessment
    rejection_reason: str | None = None
    evaluated_at: UTCDateTime = Field(default_factory=utc_now)
