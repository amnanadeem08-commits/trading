"""Paper portfolio state (PAPER-004)."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from paper_trading.contracts.ledger import PositionLedgerEntry


class PaperPortfolioState(PlatformModel):
    """Current simulated portfolio snapshot."""

    cash: float
    equity: float
    margin_used: float = Field(ge=0.0)
    free_margin: float
    open_positions: tuple[PositionLedgerEntry, ...] = ()
    closed_positions: tuple[PositionLedgerEntry, ...] = ()
    peak_equity: float = Field(gt=0.0)
    updated_at: UTCDateTime = Field(default_factory=utc_now)
