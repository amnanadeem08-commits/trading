"""Decision result contracts."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from decision.engine.decision_state import DecisionState
from models.common import PlatformModel, UTCDateTime, utc_now


class DecisionResult(PlatformModel):
    """Outcome of a decision operation."""

    decision_id: str = Field(min_length=1)
    engine_id: str = Field(min_length=1)
    policy_id: str = ""
    state: DecisionState = DecisionState.COMPLETED
    output: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    evaluation: dict[str, Any] = Field(default_factory=dict)
    version_info: dict[str, str] = Field(default_factory=dict)
    completed_at: UTCDateTime = Field(default_factory=utc_now)
