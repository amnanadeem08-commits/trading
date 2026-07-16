"""Simulated fill contracts (PAPER-004)."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime
from paper_trading.contracts.paper_order import PaperOrderSide


class FillConfig(PlatformModel):
    """Deterministic fill parameters (no randomness)."""

    slippage_bps: float = Field(ge=0.0, default=5.0)
    commission_bps: float = Field(ge=0.0, default=10.0)
    spread_bps: float = Field(ge=0.0, default=2.0)
    fill_fraction: float = Field(gt=0.0, le=1.0, default=1.0)
    initial_cash: float = Field(gt=0.0, default=100_000.0)
    default_quantity: float = Field(gt=0.0, default=1.0)


class SimulatedFill(PlatformModel):
    """Recorded outcome of a deterministic simulated fill."""

    fill_id: str = Field(min_length=1)
    trade_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    side: PaperOrderSide
    quantity: float = Field(gt=0.0)
    reference_price: float = Field(gt=0.0)
    fill_price: float = Field(gt=0.0)
    slippage: float = Field(ge=0.0)
    commission: float = Field(ge=0.0)
    spread: float = Field(ge=0.0)
    notional: float = Field(gt=0.0)
    filled_at: UTCDateTime
    deterministic: bool = True
    llm_used: bool = False
    signal_source: str = "technical_rules"
