"""Portfolio contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from models.position import NormalizedPosition


class PortfolioState(PlatformModel):
    """Current portfolio snapshot."""

    portfolio_id: str = Field(min_length=1)
    positions: tuple[NormalizedPosition, ...] = Field(default_factory=tuple)
    total_equity: float = Field(ge=0)
    total_unrealized_pnl: float = 0.0
    total_realized_pnl: float = 0.0
    currency: str = Field(min_length=3, max_length=3)
    updated_at: UTCDateTime = Field(default_factory=utc_now)
