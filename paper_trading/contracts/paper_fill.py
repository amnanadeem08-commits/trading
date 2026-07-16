"""Paper fill orchestration result (PAPER-004)."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from models.decision import DecisionState
from paper_trading.contracts.fill import SimulatedFill
from paper_trading.contracts.ledger import PnLLedgerEntry, PositionLedgerEntry
from paper_trading.contracts.paper_request import PaperSessionStatus
from paper_trading.contracts.portfolio import PaperPortfolioState


class PaperFillResult(PlatformModel):
    """Result of signal → risk gate → simulated fill."""

    session_id: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    decision: DecisionState
    status: PaperSessionStatus
    message: str = Field(min_length=1)
    fill: SimulatedFill
    position_entry: PositionLedgerEntry
    pnl_entry: PnLLedgerEntry
    portfolio: PaperPortfolioState
    risk_gate_reasons: tuple[str, ...] = ()
    created_at: UTCDateTime = Field(default_factory=utc_now)
