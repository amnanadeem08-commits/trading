"""Append-only ledger contracts (PAPER-004)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime
from paper_trading.contracts.paper_order import PaperOrderSide


class PositionStatus(StrEnum):
    """Lifecycle status for a paper position."""

    OPEN = "open"
    CLOSED = "closed"


class PositionLedgerEntry(PlatformModel):
    """Append-only position ledger row."""

    position_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    market: str = Field(min_length=1)
    side: PaperOrderSide
    quantity: float = Field(gt=0.0)
    entry_price: float = Field(gt=0.0)
    fill_price: float = Field(gt=0.0)
    status: PositionStatus
    opened_at: UTCDateTime
    closed_at: UTCDateTime | None = None
    fill_id: str = Field(min_length=1)
    trade_id: str = Field(min_length=1)


class PnLLedgerEntry(PlatformModel):
    """Append-only PnL ledger row."""

    trade_id: str = Field(min_length=1)
    position_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    market: str = Field(min_length=1)
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    commission: float = Field(ge=0.0)
    slippage: float = Field(ge=0.0)
    running_equity: float
    drawdown: float = Field(ge=0.0)
    timestamp: UTCDateTime
    fill_id: str = Field(min_length=1)
