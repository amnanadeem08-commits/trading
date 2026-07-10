"""Immutable connector capability declarations."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class RateLimitInformation(PlatformModel):
    """Provider rate limit metadata. No exchange-specific logic."""

    requests_per_second: float | None = Field(default=None, ge=0)
    requests_per_minute: float | None = Field(default=None, ge=0)
    burst_limit: int | None = Field(default=None, ge=1)
    notes: str | None = None


class ConnectorCapabilities(PlatformModel):
    """Immutable capability declaration for a connector plugin."""

    supported_markets: tuple[str, ...] = Field(min_length=1)
    supported_timeframes: tuple[str, ...] = Field(min_length=1)
    websocket_support: bool = False
    historical_support: bool = True
    pagination_support: bool = False
    order_support: bool = False
    precision_support: bool = True
    rate_limit_information: RateLimitInformation = Field(default_factory=RateLimitInformation)
