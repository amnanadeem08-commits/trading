"""Typed contracts for read-only portfolio synchronization and analysis."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel


class PortfolioWarningCode(StrEnum):
    """Non-fatal portfolio synchronization outcomes."""

    SYNC_DISABLED = "sync_disabled"
    MISSING_CREDENTIALS = "missing_credentials"
    ACCOUNT_UNAVAILABLE = "account_unavailable"
    API_TIMEOUT = "api_timeout"
    AUTHENTICATION_FAILED = "authentication_failed"
    MISSING_PAIR = "missing_pair"
    NON_TRADING_PAIR = "non_trading_pair"
    RESTRICTED_ASSET = "restricted_asset"
    PRICE_UNAVAILABLE = "price_unavailable"
    ZERO_BALANCE = "zero_balance"
    DUST_BALANCE = "dust_balance"
    QUOTE_ASSET = "quote_asset"


class PortfolioAuthenticationStatus(StrEnum):
    """Authentication result for the latest portfolio synchronization attempt."""

    NOT_ATTEMPTED = "not_attempted"
    SUCCESS = "success"
    FAILED = "failed"
    NOT_VERIFIED = "not_verified"


class PortfolioWarning(PlatformModel):
    """Structured warning that must not crash scanning or UI rendering."""

    code: PortfolioWarningCode
    message: str = Field(min_length=1)
    asset: str | None = None


class PortfolioHolding(PlatformModel):
    """Validated and valued Spot holding ready for signal projection."""

    asset: str = Field(min_length=1)
    scan_symbol: str = Field(min_length=1)
    analysis_symbol: str = Field(min_length=1)
    quantity: float = Field(gt=0.0)
    current_price: float = Field(gt=0.0)
    current_value_usdt: float = Field(ge=0.0)
    average_buy_price: float | None = Field(default=None, gt=0.0)
    floating_pnl: float | None = None
    floating_pnl_percent: float | None = None
    analysis_explanation: str | None = None
    holding_type: str = "Spot"
    is_stable_balance: bool = False


class PortfolioSyncDiagnostics(PlatformModel):
    """Non-sensitive stage counts and connection state for dashboard diagnostics."""

    portfolio_sync_enabled: bool = False
    credentials_loaded: bool = False
    fetch_balance_executed: bool = False
    fetch_balance_success: bool = False
    binance_connected: bool = False
    authentication_status: PortfolioAuthenticationStatus = (
        PortfolioAuthenticationStatus.NOT_ATTEMPTED
    )
    non_zero_balance_count: int = Field(ge=0, default=0)
    asset_symbols_returned: tuple[str, ...] = Field(default_factory=tuple)
    mapped_asset_count: int = Field(ge=0, default=0)
    valid_market_count: int = Field(ge=0, default=0)
    successfully_valued_count: int = Field(ge=0, default=0)
    above_threshold_count: int = Field(ge=0, default=0)
    final_holding_count: int = Field(ge=0, default=0)

    @property
    def holdings_returned(self) -> int:
        """Compatibility accessor for earlier diagnostics consumers."""
        return self.non_zero_balance_count

    @property
    def holdings_after_market_validation(self) -> int:
        return self.valid_market_count

    @property
    def holdings_after_value_filter(self) -> int:
        return self.above_threshold_count

    @property
    def final_portfolio_holdings(self) -> int:
        return self.final_holding_count


class PortfolioSyncResult(PlatformModel):
    """Complete fail-soft portfolio synchronization result."""

    holdings: tuple[PortfolioHolding, ...] = Field(default_factory=tuple)
    warnings: tuple[PortfolioWarning, ...] = Field(default_factory=tuple)
    diagnostics: PortfolioSyncDiagnostics = Field(default_factory=PortfolioSyncDiagnostics)

    @property
    def portfolio_symbols(self) -> tuple[str, ...]:
        """Return canonical symbols required by the scanner."""
        return tuple(holding.scan_symbol for holding in self.holdings)

    @property
    def sync_succeeded(self) -> bool:
        """Return whether balance retrieval completed without a fatal sync failure."""
        diagnostics = self.diagnostics
        return diagnostics.fetch_balance_success and (
            diagnostics.authentication_status == PortfolioAuthenticationStatus.SUCCESS
        )


class PortfolioSignalRow(PlatformModel):
    """Advisory portfolio analysis row rendered by Streamlit."""

    asset: str
    analysis_symbol: str
    quantity: float
    current_price: float
    current_value_usdt: float
    average_buy_price: float | None = None
    floating_pnl: float | None = None
    floating_pnl_percent: float | None = None
    signal: str
    confidence: str
    entry_zone: str | float | None = None
    stop_loss: str | float | None = None
    take_profit: str | float | None = None
    reasoning: str
    suggested_action: str
