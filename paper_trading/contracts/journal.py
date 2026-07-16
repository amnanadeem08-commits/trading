"""Paper trading journal and review contracts (PAPER-006).

Disclaimer: journal entries and review notes are for simulated trade review and
learning only. They are **not** financial advice and do not guarantee profits.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from models.decision import DecisionState
from paper_trading.contracts.paper_order import PaperOrderSide
from paper_trading.contracts.paper_request import PaperSessionStatus


class PaperJournalTradeState(StrEnum):
    """Review-oriented trade state for a paper journal entry."""

    REJECTED = "rejected"
    CANCELLED = "cancelled"
    OPEN = "open"
    CLOSED = "closed"


class PaperJournalReviewNote(PlatformModel):
    """Append-only post-trade review annotation (not financial advice)."""

    review_id: str = Field(min_length=1)
    journal_id: str = Field(min_length=1)
    tags: tuple[str, ...] = ()
    lesson: str = ""
    notes: str = ""
    created_at: UTCDateTime = Field(default_factory=utc_now)


class PaperJournalEntry(PlatformModel):
    """Append-only journal record linking signal through fill, position, and P&L."""

    journal_id: str = Field(min_length=1)
    session_id: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    fill_id: str | None = None
    position_id: str | None = None
    trade_id: str | None = None
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    timeframe: str = Field(min_length=1)
    direction: DecisionState
    side: PaperOrderSide | None = None
    trade_state: PaperJournalTradeState
    lifecycle_status: str = Field(min_length=1)
    session_status: PaperSessionStatus
    risk_decision: DecisionState
    risk_gate_passed: bool | None = None
    risk_gate_reasons: tuple[str, ...] = ()
    recorded_at: UTCDateTime
    filled_at: UTCDateTime | None = None
    closed_at: UTCDateTime | None = None
    entry_price: float | None = Field(default=None, gt=0.0)
    exit_price: float | None = Field(default=None, gt=0.0)
    fill_price: float | None = Field(default=None, gt=0.0)
    stop_price: float | None = Field(default=None, gt=0.0)
    target_price: float | None = Field(default=None, gt=0.0)
    commission: float = Field(ge=0.0, default=0.0)
    slippage: float = Field(ge=0.0, default=0.0)
    fees: float = Field(ge=0.0, default=0.0)
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    validation_outcome: str | None = None
    explanatory_notes: str = ""


class PaperJournalFilter(PlatformModel):
    """Optional criteria for listing and summarizing journal entries."""

    session_id: str | None = None
    signal_id: str | None = None
    fill_id: str | None = None
    position_id: str | None = None
    symbol_id: str | None = None
    market_id: str | None = None
    timeframe: str | None = None
    trade_state: PaperJournalTradeState | None = None
    direction: DecisionState | None = None


class PaperJournalSummary(PlatformModel):
    """Aggregated review summary over a filtered journal slice."""

    total_entries: int = Field(ge=0)
    rejected_count: int = Field(ge=0)
    cancelled_count: int = Field(ge=0)
    open_count: int = Field(ge=0)
    closed_count: int = Field(ge=0)
    total_realized_pnl: float = 0.0
    total_unrealized_pnl: float = 0.0
    total_commission: float = Field(ge=0.0, default=0.0)
    total_fees: float = Field(ge=0.0, default=0.0)
    symbol_ids: tuple[str, ...] = ()


class PaperPerformanceMetrics(PlatformModel):
    """Deterministic performance metrics for simulated paper trades (PAPER-007).

    Disclaimer: metrics reflect simulated outcomes only — not financial advice.
    """

    total_simulated_trades: int = Field(ge=0)
    open_trades: int = Field(ge=0)
    closed_trades: int = Field(ge=0)
    rejected_trades: int = Field(ge=0)
    cancelled_trades: int = Field(ge=0)
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    breakeven_trades: int = Field(ge=0)
    win_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    total_fees: float = Field(ge=0.0, default=0.0)
    average_return_pct: float | None = None
    average_risk_reward: float | None = None
    max_drawdown: float | None = Field(default=None, ge=0.0)
    signal_accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
