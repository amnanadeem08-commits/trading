"""Compatibility tests: backtesting vs paper-trading fill assumptions."""

from __future__ import annotations

import pytest

from backtesting.contracts.config import BacktestConfig
from backtesting.engine.pricing import (
    compute_commission as backtest_commission,
)
from backtesting.engine.pricing import (
    compute_fill_price as backtest_fill_price,
)
from models.decision import DecisionState
from paper_trading.contracts.fill import FillConfig
from paper_trading.contracts.paper_order import PaperOrderSide
from paper_trading.fill.engine import compute_commission as paper_commission
from paper_trading.fill.engine import compute_fill_price as paper_fill_price


@pytest.mark.unit
@pytest.mark.parametrize(
    ("reference_price", "direction", "side"),
    [
        (100.0, DecisionState.BUY, PaperOrderSide.BUY),
        (250.75, DecisionState.SELL, PaperOrderSide.SELL),
    ],
)
def test_fill_price_parity_between_backtest_and_paper(
    reference_price: float,
    direction: DecisionState,
    side: PaperOrderSide,
) -> None:
    backtest_config = BacktestConfig()
    paper_config = FillConfig(
        slippage_bps=backtest_config.slippage_bps,
        commission_bps=backtest_config.commission_bps,
        spread_bps=backtest_config.spread_bps,
    )

    bt_fill, bt_spread, bt_slip = backtest_fill_price(
        reference_price,
        direction,
        spread_bps=backtest_config.spread_bps,
        slippage_bps=backtest_config.slippage_bps,
    )
    paper_fill, paper_spread, paper_slip = paper_fill_price(
        reference_price,
        side,
        config=paper_config,
    )

    assert bt_fill == pytest.approx(paper_fill)
    assert bt_spread == pytest.approx(paper_spread)
    assert bt_slip == pytest.approx(paper_slip)


@pytest.mark.unit
def test_commission_parity_between_backtest_and_paper() -> None:
    backtest_config = BacktestConfig()
    notional = 10_000.0
    assert backtest_commission(notional, backtest_config.commission_bps) == pytest.approx(
        paper_commission(notional, backtest_config.commission_bps)
    )


@pytest.mark.unit
def test_default_bps_assumptions_match_paper_fill_config() -> None:
    backtest_config = BacktestConfig()
    paper_config = FillConfig()

    assert backtest_config.slippage_bps == paper_config.slippage_bps
    assert backtest_config.commission_bps == paper_config.commission_bps
    assert backtest_config.spread_bps == paper_config.spread_bps
    assert backtest_config.initial_cash == paper_config.initial_cash
    assert backtest_config.default_quantity == paper_config.default_quantity
