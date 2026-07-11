"""Typed paper order request mapped from ExplainableSignal."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel
from models.decision import DecisionSource, DecisionState


class PaperOrderSide(StrEnum):
    """Paper-side intent derived from signal decision (not a live broker order)."""

    BUY = "BUY"
    SELL = "SELL"
    FLAT = "FLAT"


class PaperOrderRequest(PlatformModel):
    """Paper adapter-oriented order request built from an explainable signal."""

    request_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    side: PaperOrderSide
    decision: DecisionState
    decision_source: DecisionSource
    confidence: float = Field(ge=0.0, le=1.0)
    reference_price: float | None = Field(default=None, gt=0)
    quantity: float | None = Field(default=None, gt=0)
    invalidation_condition: str = Field(min_length=1)
    risk_exposure_impact: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    feature_snapshot_version: str = Field(min_length=1)
    adapter_payload: dict[str, object] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)


class PaperOrderMappingResult(PlatformModel):
    """Accept/reject outcome for signal → paper order mapping."""

    passed: bool
    reasons: tuple[str, ...] = Field(default_factory=tuple)
    order: PaperOrderRequest | None = None
