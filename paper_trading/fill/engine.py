"""Deterministic fill price math (no randomness)."""

from __future__ import annotations

from paper_trading.contracts.fill import FillConfig
from paper_trading.contracts.paper_order import PaperOrderSide


def _bps_factor(bps: float) -> float:
    return bps / 10_000.0


def compute_spread_amount(reference_price: float, spread_bps: float) -> float:
    """Half-spread impact per side in price units."""
    return reference_price * _bps_factor(spread_bps)


def compute_slippage_amount(fill_price_before_slippage: float, slippage_bps: float) -> float:
    """Slippage cost in price units (adverse direction already applied in fill_price)."""
    return fill_price_before_slippage * _bps_factor(slippage_bps)


def compute_fill_price(
    reference_price: float,
    side: PaperOrderSide,
    *,
    config: FillConfig,
) -> tuple[float, float, float]:
    """Return (fill_price, spread_amount, slippage_amount). Deterministic."""
    spread_amt = compute_spread_amount(reference_price, config.spread_bps)
    if side == PaperOrderSide.BUY:
        after_spread = reference_price + spread_amt
        slippage_amt = compute_slippage_amount(after_spread, config.slippage_bps)
        fill_price = after_spread + slippage_amt
    elif side == PaperOrderSide.SELL:
        after_spread = reference_price - spread_amt
        slippage_amt = compute_slippage_amount(after_spread, config.slippage_bps)
        fill_price = after_spread - slippage_amt
    else:
        fill_price = reference_price
        slippage_amt = 0.0
    return fill_price, spread_amt, slippage_amt


def compute_commission(notional: float, commission_bps: float) -> float:
    return notional * _bps_factor(commission_bps)
