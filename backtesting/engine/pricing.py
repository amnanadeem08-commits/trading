"""Deterministic fill pricing (mirrors paper fill math without importing paper_trading)."""

from __future__ import annotations

from models.decision import DecisionState


def _bps_factor(bps: float) -> float:
    return bps / 10_000.0


def compute_spread_amount(reference_price: float, spread_bps: float) -> float:
    return reference_price * _bps_factor(spread_bps)


def compute_slippage_amount(fill_price_before_slippage: float, slippage_bps: float) -> float:
    return fill_price_before_slippage * _bps_factor(slippage_bps)


def compute_commission(notional: float, commission_bps: float) -> float:
    return notional * _bps_factor(commission_bps)


def compute_fill_price(
    reference_price: float,
    direction: DecisionState,
    *,
    spread_bps: float,
    slippage_bps: float,
) -> tuple[float, float, float]:
    """Return (fill_price, spread_amount, slippage_amount)."""
    spread_amt = compute_spread_amount(reference_price, spread_bps)
    if direction == DecisionState.BUY:
        after_spread = reference_price + spread_amt
        slippage_amt = compute_slippage_amount(after_spread, slippage_bps)
        fill_price = after_spread + slippage_amt
    elif direction == DecisionState.SELL:
        after_spread = reference_price - spread_amt
        slippage_amt = compute_slippage_amount(after_spread, slippage_bps)
        fill_price = after_spread - slippage_amt
    else:
        fill_price = reference_price
        slippage_amt = 0.0
    return fill_price, spread_amt, slippage_amt
