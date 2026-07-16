"""Project scanner signals onto validated portfolio holdings."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from portfolio_sync.contracts import PortfolioHolding, PortfolioSignalRow


def project_portfolio_signals(
    holdings: Sequence[PortfolioHolding],
    signal_rows: Sequence[Mapping[str, object]],
) -> tuple[PortfolioSignalRow, ...]:
    """Join each holding to its existing scanner result without re-analysis."""
    by_symbol = {
        _compact(str(row.get("symbol", ""))): row
        for row in signal_rows
        if str(row.get("symbol", "")).strip()
    }
    projected: list[PortfolioSignalRow] = []
    for holding in holdings:
        # Skip stable balances (LDUSDT) - they appear in holdings but not signals
        if holding.is_stable_balance:
            continue
        signal_row = by_symbol.get(_compact(holding.scan_symbol), {})
        signal = str(signal_row.get("signal", "N/A")).upper()
        reasoning = str(signal_row.get("reasoning", "No scanner signal is available."))
        if holding.analysis_explanation:
            reasoning = f"{holding.analysis_explanation} {reasoning}".strip()
        projected.append(
            PortfolioSignalRow(
                asset=holding.asset,
                analysis_symbol=holding.analysis_symbol,
                quantity=holding.quantity,
                current_price=holding.current_price,
                current_value_usdt=holding.current_value_usdt,
                average_buy_price=holding.average_buy_price,
                floating_pnl=holding.floating_pnl,
                floating_pnl_percent=holding.floating_pnl_percent,
                signal=signal,
                confidence=str(signal_row.get("confidence", "N/A")),
                entry_zone=_optional_level(signal_row.get("entry_zone")),
                stop_loss=_optional_level(signal_row.get("stop_loss")),
                take_profit=_optional_level(signal_row.get("take_profit")),
                reasoning=reasoning,
                suggested_action=_suggested_action(signal),
            )
        )
    return tuple(projected)


def portfolio_rows_for_display(
    rows: Sequence[PortfolioSignalRow],
) -> list[dict[str, object]]:
    """Return table-ready dictionaries with unavailable optional values as N/A."""
    rendered: list[dict[str, object]] = []
    for row in rows:
        payload = row.model_dump(mode="python")
        for key in (
            "average_buy_price",
            "floating_pnl",
            "floating_pnl_percent",
            "entry_zone",
            "stop_loss",
            "take_profit",
        ):
            if payload[key] is None:
                payload[key] = "N/A"
        rendered.append(payload)
    return rendered


def _compact(symbol: str) -> str:
    return symbol.replace("/", "").replace("-", "").upper()


def _optional_level(value: object) -> str | float | None:
    if isinstance(value, (str, float, int)) and not isinstance(value, bool):
        return float(value) if isinstance(value, int) else value
    return None


def _suggested_action(signal: str) -> str:
    actions = {
        "BUY": "Review adding exposure; no trade is placed.",
        "SELL": "Review reducing exposure; no trade is placed.",
        "HOLD": "Continue monitoring; no trade is placed.",
    }
    return actions.get(signal, "No signal available; continue monitoring.")
