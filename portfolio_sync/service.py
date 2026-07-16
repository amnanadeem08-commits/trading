"""Fail-soft read-only Binance Spot portfolio synchronization."""

from __future__ import annotations

from typing import Protocol

from config.settings import PortfolioSyncSettings
from connectors.binance_spot_portfolio import (
    MarketEligibility,
    PortfolioAuthenticationError,
    PortfolioGatewayError,
    PortfolioTimeoutError,
    SpotBalance,
)
from portfolio_sync.contracts import (
    PortfolioAuthenticationStatus,
    PortfolioHolding,
    PortfolioSyncDiagnostics,
    PortfolioSyncResult,
    PortfolioWarning,
    PortfolioWarningCode,
)


class PortfolioGateway(Protocol):
    """Injected read-only gateway required by the domain service."""

    def fetch_balances(self) -> tuple[SpotBalance, ...]: ...

    def validate_spot_market(self, symbol: str) -> MarketEligibility: ...

    def fetch_prices(self, symbols: tuple[str, ...]) -> dict[str, float]: ...


class PortfolioSyncService:
    """Convert Binance balances into validated, non-dust portfolio holdings."""

    def __init__(
        self,
        gateway: PortfolioGateway,
        settings: PortfolioSyncSettings,
    ) -> None:
        self._gateway = gateway
        self._settings = settings

    def sync(self) -> PortfolioSyncResult:
        """Synchronize holdings; all provider failures become structured warnings."""
        if not self._settings.enabled:
            return PortfolioSyncResult(
                diagnostics=PortfolioSyncDiagnostics(portfolio_sync_enabled=False)
            )
        attempted = PortfolioSyncDiagnostics(
            portfolio_sync_enabled=True,
            credentials_loaded=True,
            fetch_balance_executed=True,
        )
        try:
            balances = self._gateway.fetch_balances()
        except PortfolioAuthenticationError as error:
            return _failure(
                PortfolioWarningCode.AUTHENTICATION_FAILED,
                f"Binance authentication failed: {error}",
                diagnostics=attempted.model_copy(
                    update={
                        "authentication_status": PortfolioAuthenticationStatus.FAILED,
                    }
                ),
            )
        except PortfolioTimeoutError as error:
            return _failure(
                PortfolioWarningCode.API_TIMEOUT,
                str(error),
                diagnostics=attempted.model_copy(
                    update={
                        "authentication_status": PortfolioAuthenticationStatus.NOT_VERIFIED,
                    }
                ),
            )
        except (PortfolioGatewayError, TypeError, ValueError) as error:
            return _failure(
                PortfolioWarningCode.ACCOUNT_UNAVAILABLE,
                str(error),
                diagnostics=attempted.model_copy(
                    update={
                        "authentication_status": PortfolioAuthenticationStatus.NOT_VERIFIED,
                    }
                ),
            )

        return self._build_result(balances)

    def _build_result(self, balances: tuple[SpotBalance, ...]) -> PortfolioSyncResult:
        holdings: list[PortfolioHolding] = []
        warnings: list[PortfolioWarning] = []
        quote_asset = self._settings.quote_asset.upper()
        mappings = {
            asset.upper(): symbol.upper()
            for asset, symbol in self._settings.asset_analysis_mapping.items()
        }
        eligible_assets: list[tuple[SpotBalance, str]] = []
        mapped_asset_count = 0
        non_zero_assets: list[SpotBalance] = []

        for balance in balances:
            asset = balance.asset.upper()
            if balance.quantity <= 0.0:
                warnings.append(
                    _warning(
                        PortfolioWarningCode.ZERO_BALANCE,
                        asset,
                        f"Ignored zero balance for {asset}.",
                    )
                )
                continue
            non_zero_assets.append(balance)
            if asset == quote_asset:
                warnings.append(
                    _warning(
                        PortfolioWarningCode.QUOTE_ASSET,
                        asset,
                        (
                            f"Ignored {asset}: the quote-asset cash balance does not "
                            f"have a {asset}/{quote_asset} analysis market."
                        ),
                    )
                )
                continue
            scan_symbol = mappings.get(asset, f"{asset}/{quote_asset}")
            if asset in mappings:
                mapped_asset_count += 1
            try:
                eligibility = self._gateway.validate_spot_market(scan_symbol)
            except PortfolioTimeoutError as error:
                warnings.append(_warning(PortfolioWarningCode.API_TIMEOUT, asset, str(error)))
                continue
            except PortfolioGatewayError as error:
                warnings.append(
                    _warning(PortfolioWarningCode.ACCOUNT_UNAVAILABLE, asset, str(error))
                )
                continue
            if not eligibility.eligible:
                warnings.append(_eligibility_warning(asset, scan_symbol, eligibility.reason))
                continue
            eligible_assets.append((balance, scan_symbol))

        prices: dict[str, float] = {}
        if eligible_assets:
            symbols = tuple(symbol for _, symbol in eligible_assets)
            try:
                prices = self._gateway.fetch_prices(symbols)
            except PortfolioTimeoutError as error:
                warnings.append(_warning(PortfolioWarningCode.API_TIMEOUT, None, str(error)))
            except PortfolioGatewayError as error:
                warnings.append(
                    _warning(PortfolioWarningCode.PRICE_UNAVAILABLE, None, str(error))
                )

        successfully_valued_count = 0
        above_threshold_count = 0
        for balance, scan_symbol in eligible_assets:
            asset = balance.asset.upper()
            price = prices.get(scan_symbol)
            if price is None:
                warnings.append(
                    _warning(
                        PortfolioWarningCode.PRICE_UNAVAILABLE,
                        asset,
                        f"Ticker valuation failed for {asset} ({scan_symbol}).",
                    )
                )
                continue
            successfully_valued_count += 1
            value = balance.quantity * price
            if value < self._settings.minimum_holding_usdt:
                warnings.append(
                    _warning(
                        PortfolioWarningCode.DUST_BALANCE,
                        asset,
                        (
                            f"Ignored {asset} holding valued at {value:.8f} USDT; "
                            f"minimum is {self._settings.minimum_holding_usdt:.2f} USDT."
                        ),
                    )
                )
                continue
            above_threshold_count += 1
            
            # Detect holding type and generate explanation
            holding_type = "Spot"
            is_stable = False
            if asset in mappings:
                underlying = scan_symbol.split("/")[0]
                if asset.startswith("LD"):
                    holding_type = "Binance Earn"
                    if asset == "LDUSDT":
                        is_stable = True
                        explanation = (
                            "This is a Binance Earn/locked USDT position. "
                            "Value shown is estimated; no market analysis is performed for stablecoins."
                        )
                    else:
                        explanation = (
                            f"This is a Binance Earn/locked position. "
                            f"Market analysis is based on {scan_symbol}."
                        )
                elif asset == "BNSOL":
                    explanation = f"Market analysis is based on {scan_symbol}."
                else:
                    explanation = f"Market analysis is based on {scan_symbol}."
            else:
                explanation = None
            
            holdings.append(
                PortfolioHolding(
                    asset=asset,
                    scan_symbol=scan_symbol,
                    analysis_symbol=scan_symbol.replace("/", ""),
                    quantity=balance.quantity,
                    current_price=price,
                    current_value_usdt=value,
                    analysis_explanation=explanation,
                    holding_type=holding_type,
                    is_stable_balance=is_stable,
                )
            )

        asset_symbols = tuple(balance.asset for balance in non_zero_assets)
        return PortfolioSyncResult(
            holdings=tuple(holdings),
            warnings=tuple(warnings),
            diagnostics=PortfolioSyncDiagnostics(
                portfolio_sync_enabled=True,
                credentials_loaded=True,
                fetch_balance_executed=True,
                fetch_balance_success=True,
                binance_connected=True,
                authentication_status=PortfolioAuthenticationStatus.SUCCESS,
                non_zero_balance_count=len(non_zero_assets),
                asset_symbols_returned=asset_symbols,
                mapped_asset_count=mapped_asset_count,
                valid_market_count=len(eligible_assets),
                successfully_valued_count=successfully_valued_count,
                above_threshold_count=above_threshold_count,
                final_holding_count=len(holdings),
            ),
        )


def unavailable_result(
    code: PortfolioWarningCode,
    message: str,
    *,
    diagnostics: PortfolioSyncDiagnostics | None = None,
) -> PortfolioSyncResult:
    """Build a non-fatal result when synchronization cannot start."""
    return _failure(code, message, diagnostics=diagnostics)


def portfolio_stage_message(
    result: PortfolioSyncResult,
    *,
    from_cache: bool = False,
) -> str:
    """Return a user-facing portfolio sync stage message without exposing secrets."""
    diagnostics = result.diagnostics
    if not diagnostics.portfolio_sync_enabled:
        return "Portfolio sync is disabled in config/portfolio_sync.yaml."
    if not diagnostics.credentials_loaded:
        return "Binance credentials were not loaded."
    if diagnostics.authentication_status == PortfolioAuthenticationStatus.FAILED:
        auth_warning = next(
            (
                warning.message
                for warning in result.warnings
                if warning.code == PortfolioWarningCode.AUTHENTICATION_FAILED
            ),
            None,
        )
        if auth_warning:
            return auth_warning
        return "Binance authentication failed."
    if any(warning.code == PortfolioWarningCode.API_TIMEOUT for warning in result.warnings):
        if from_cache:
            return "Portfolio sync timed out; showing last cached result."
        return "Portfolio sync timed out before holdings could be valued."
    if not diagnostics.fetch_balance_executed:
        return "Portfolio sync has not run yet. Click Refresh Results."
    if diagnostics.non_zero_balance_count == 0:
        return "Binance returned no non-zero Spot holdings."
    if diagnostics.final_holding_count == 0 and diagnostics.successfully_valued_count == 0:
        if diagnostics.valid_market_count == 0 and diagnostics.non_zero_balance_count > 0:
            filtered = diagnostics.non_zero_balance_count
            return (
                f"{diagnostics.non_zero_balance_count} assets found; "
                f"{filtered} were removed by market validation or dust filtering."
            )
        return (
            f"{diagnostics.non_zero_balance_count} non-zero assets found, "
            "but ticker valuation failed."
        )
    if diagnostics.final_holding_count == 0 and diagnostics.above_threshold_count == 0:
        below_threshold = diagnostics.successfully_valued_count
        if below_threshold > 0:
            return (
                f"{diagnostics.non_zero_balance_count} assets found; "
                f"{below_threshold} were below the configured threshold."
            )
        filtered = diagnostics.non_zero_balance_count - diagnostics.final_holding_count
        return (
            f"{diagnostics.non_zero_balance_count} assets found; "
            f"{filtered} were removed by market validation or dust filtering."
        )
    if from_cache:
        return "Showing last cached portfolio sync result."
    return (
        f"Portfolio sync completed with {diagnostics.final_holding_count} "
        f"holding{'s' if diagnostics.final_holding_count != 1 else ''}."
    )


def _failure(
    code: PortfolioWarningCode,
    message: str,
    *,
    diagnostics: PortfolioSyncDiagnostics | None = None,
) -> PortfolioSyncResult:
    return PortfolioSyncResult(
        warnings=(PortfolioWarning(code=code, message=message),),
        diagnostics=diagnostics or PortfolioSyncDiagnostics(),
    )


def _warning(
    code: PortfolioWarningCode,
    asset: str | None,
    message: str,
) -> PortfolioWarning:
    return PortfolioWarning(code=code, asset=asset, message=message)


def _eligibility_warning(
    asset: str,
    symbol: str,
    reason: str | None,
) -> PortfolioWarning:
    if reason == "missing_pair":
        code = PortfolioWarningCode.MISSING_PAIR
    elif reason == "restricted_asset":
        code = PortfolioWarningCode.RESTRICTED_ASSET
    else:
        code = PortfolioWarningCode.NON_TRADING_PAIR
    return _warning(code, asset, f"Ignored {asset}: {symbol} is not eligible ({reason}).")
