"""Contracts for paper trading orchestration inputs."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from models.decision import DecisionState
from models.signal import ExplainableSignal


class PaperSessionStatus(StrEnum):
    """Lifecycle status for a paper trading session (fill comes in later tasks)."""

    PREPARED = "prepared"
    RISK_APPROVED = "risk_approved"
    RISK_REJECTED = "risk_rejected"
    REJECTED = "rejected"
    # Later: FILLED, CANCELLED (PAPER-004+)


class PaperOrchestrationRequest(PlatformModel):
    """Typed request to enter the paper path from an explainable signal."""

    session_id: str = Field(min_length=1)
    signal: ExplainableSignal
    notes: str = ""


class PaperOrchestrationResult(PlatformModel):
    """Result of paper orchestration (skeleton — no simulated fill yet)."""

    session_id: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    decision: DecisionState
    status: PaperSessionStatus
    message: str = Field(min_length=1)
    risk_gate_reasons: tuple[str, ...] = ()
    created_at: UTCDateTime = Field(default_factory=utc_now)
