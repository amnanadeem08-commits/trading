"""Order contracts. Market-agnostic."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(StrEnum):
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderRequest(PlatformModel):
    """Platform order request. Connectors/brokers translate to venue format."""

    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    side: OrderSide
    order_type: OrderType
    quantity: float = Field(gt=0)
    price: float | None = Field(default=None, gt=0)
    client_order_id: str | None = None


class NormalizedOrder(PlatformModel):
    """Normalized order state from any connector or broker."""

    order_id: str = Field(min_length=1)
    client_order_id: str | None = None
    symbol_id: str = Field(min_length=1)
    market_id: str = Field(min_length=1)
    side: OrderSide
    order_type: OrderType
    status: OrderStatus
    quantity: float = Field(gt=0)
    filled_quantity: float = Field(ge=0, default=0)
    price: float | None = Field(default=None, gt=0)
    average_fill_price: float | None = Field(default=None, gt=0)
    created_at: UTCDateTime = Field(default_factory=utc_now)
    updated_at: UTCDateTime = Field(default_factory=utc_now)
