"""Unit tests for append-only ledgers (PAPER-004)."""

from __future__ import annotations

import pytest

from models.common import utc_now
from paper_trading.contracts.ledger import PositionLedgerEntry, PositionStatus
from paper_trading.contracts.paper_order import PaperOrderSide
from paper_trading.ledger.pnl_ledger import PnLLedger
from paper_trading.ledger.position_ledger import PositionLedger


def _position(status: PositionStatus = PositionStatus.OPEN) -> PositionLedgerEntry:
    now = utc_now()
    return PositionLedgerEntry(
        position_id="pos-1",
        symbol="BTC/USDT",
        market="crypto",
        side=PaperOrderSide.BUY,
        quantity=1.0,
        entry_price=100.0,
        fill_price=100.5,
        status=status,
        opened_at=now,
        closed_at=now if status == PositionStatus.CLOSED else None,
        fill_id="fill-1",
        trade_id="trade-1",
    )


@pytest.mark.unit
def test_position_ledger_append_only() -> None:
    ledger = PositionLedger()
    first = ledger.append(_position())
    ledger.append(_position(status=PositionStatus.CLOSED))
    assert len(ledger.entries()) == 2
    assert ledger.entries()[0] is first
    assert ledger.open_for_symbol("BTC/USDT") is first


@pytest.mark.unit
def test_pnl_ledger_append_only() -> None:
    from paper_trading.contracts.ledger import PnLLedgerEntry

    ledger = PnLLedger()
    now = utc_now()
    row = PnLLedgerEntry(
        trade_id="t1",
        position_id="p1",
        symbol="BTC/USDT",
        market="crypto",
        realized_pnl=0.0,
        unrealized_pnl=0.0,
        commission=1.0,
        slippage=0.5,
        running_equity=100_000.0,
        drawdown=0.0,
        timestamp=now,
        fill_id="f1",
    )
    ledger.append(row)
    assert ledger.last() is row
    assert len(ledger.entries()) == 1
