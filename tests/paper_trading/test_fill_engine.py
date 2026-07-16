"""Unit tests for deterministic fill engine (PAPER-004)."""

from __future__ import annotations

import pytest

from models.common import utc_now
from models.decision import DecisionState
from paper_trading.contracts.fill import FillConfig
from paper_trading.contracts.paper_order import PaperOrderSide
from paper_trading.fill.engine import compute_commission, compute_fill_price
from paper_trading.fill.executor import SimulatedFillExecutor
from paper_trading.mapping.signal_mapper import map_signal_to_paper_order
from signal_engine import SignalAssembler
from tests.signal_helpers import make_assembly_request


def _buy_order(price: float = 100.0, qty: float = 2.0):
    signal = SignalAssembler().assemble(
        make_assembly_request(
            signal_id="sig-fill-1",
            decision=DecisionState.BUY,
            confidence=0.7,
            indicator_values={"rsi_14": 40.0, "close": price},
        )
    )
    result = map_signal_to_paper_order(signal, session_id="ps-fill-1", quantity=qty)
    assert result.passed and result.order is not None
    return result.order


@pytest.mark.unit
def test_fill_price_buy_includes_spread_and_slippage() -> None:
    cfg = FillConfig(slippage_bps=10.0, spread_bps=4.0, commission_bps=0.0)
    price, spread, slip = compute_fill_price(100.0, PaperOrderSide.BUY, config=cfg)
    assert spread == pytest.approx(0.04)
    assert price > 100.04
    assert slip == pytest.approx(price - 100.04, rel=1e-6)


@pytest.mark.unit
def test_fill_price_sell_subtracts_spread_and_slippage() -> None:
    cfg = FillConfig(slippage_bps=10.0, spread_bps=4.0)
    price, _, _ = compute_fill_price(100.0, PaperOrderSide.SELL, config=cfg)
    assert price < 99.96


@pytest.mark.unit
def test_commission_deterministic() -> None:
    assert compute_commission(10_000.0, 10.0) == pytest.approx(10.0)


@pytest.mark.unit
def test_same_input_same_fill_output() -> None:
    cfg = FillConfig(slippage_bps=5.0, spread_bps=2.0, commission_bps=10.0)
    ts = utc_now()
    order = _buy_order()
    ex1 = SimulatedFillExecutor(config=cfg)
    ex2 = SimulatedFillExecutor(config=cfg)
    r1 = ex1.execute(order, timestamp=ts)
    r2 = ex2.execute(order, timestamp=ts)
    assert r1.fill.fill_id == r2.fill.fill_id
    assert r1.fill.fill_price == r2.fill.fill_price
    assert r1.fill.commission == r2.fill.commission
    assert r1.pnl_entry.running_equity == r2.pnl_entry.running_equity


@pytest.mark.unit
def test_partial_fill_fraction() -> None:
    cfg = FillConfig(fill_fraction=1.0, default_quantity=10.0)
    order = _buy_order(qty=10.0)
    ex = SimulatedFillExecutor(config=cfg)
    full = ex.execute(order, fill_fraction=1.0)
    partial = ex.execute(order, fill_fraction=0.5)
    assert partial.fill.quantity == pytest.approx(5.0)
    assert partial.fill.notional < full.fill.notional
