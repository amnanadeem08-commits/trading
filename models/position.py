"""Position and account contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class NormalizedPosition(PlatformModel):
    """Normalized open position."""

    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    quantity: float
    average_price: float = Field(gt=0)
    unrealized_pnl: float | None = None
    realized_pnl: float | None = None
    updated_at: UTCDateTime = Field(default_factory=utc_now)


class NormalizedAccount(PlatformModel):
    """Normalized account snapshot."""

    market_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    balance: float = Field(ge=0)
    equity: float = Field(ge=0)
    margin_used: float = Field(ge=0, default=0)
    margin_available: float = Field(ge=0, default=0)
    currency: str = Field(min_length=3, max_length=3)
    updated_at: UTCDateTime = Field(default_factory=utc_now)
