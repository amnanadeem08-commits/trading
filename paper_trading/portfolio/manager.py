"""Paper portfolio manager (PAPER-004)."""

from __future__ import annotations

from threading import RLock

from models.common import UTCDateTime
from paper_trading.contracts.fill import FillConfig
from paper_trading.contracts.ledger import PnLLedgerEntry, PositionLedgerEntry, PositionStatus
from paper_trading.contracts.paper_order import PaperOrderSide
from paper_trading.contracts.portfolio import PaperPortfolioState
from paper_trading.ledger.pnl_ledger import PnLLedger
from paper_trading.ledger.position_ledger import PositionLedger


class PaperPortfolioManager:
    """Maintains cash/equity from append-only ledgers."""

    def __init__(
        self,
        *,
        config: FillConfig,
        position_ledger: PositionLedger | None = None,
        pnl_ledger: PnLLedger | None = None,
    ) -> None:
        self._config = config
        self._position_ledger = position_ledger or PositionLedger()
        self._pnl_ledger = pnl_ledger or PnLLedger()
        self._lock = RLock()
        self._cash = config.initial_cash
        self._peak_equity = config.initial_cash

    @property
    def cash(self) -> float:
        with self._lock:
            return self._cash

    @property
    def position_ledger(self) -> PositionLedger:
        return self._position_ledger

    @property
    def pnl_ledger(self) -> PnLLedger:
        return self._pnl_ledger

    def apply_open(
        self,
        *,
        position_id: str,
        trade_id: str,
        fill_id: str,
        symbol: str,
        market: str,
        side: PaperOrderSide,
        quantity: float,
        entry_price: float,
        fill_price: float,
        commission: float,
        slippage: float,
        timestamp: UTCDateTime,
    ) -> tuple[PositionLedgerEntry, PnLLedgerEntry, PaperPortfolioState]:
        """Open a new position and record PnL snapshot."""
        notional = quantity * fill_price
        with self._lock:
            if side == PaperOrderSide.BUY:
                self._cash -= notional + commission
            elif side == PaperOrderSide.SELL:
                self._cash += notional - commission

            position = PositionLedgerEntry(
                position_id=position_id,
                symbol=symbol,
                market=market,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                fill_price=fill_price,
                status=PositionStatus.OPEN,
                opened_at=timestamp,
                closed_at=None,
                fill_id=fill_id,
                trade_id=trade_id,
            )
            self._position_ledger.append(position)
            equity = self._compute_equity()
            self._peak_equity = max(self._peak_equity, equity)
            drawdown = max(0.0, self._peak_equity - equity)
            pnl_row = PnLLedgerEntry(
                trade_id=trade_id,
                position_id=position_id,
                symbol=symbol,
                market=market,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
                commission=commission,
                slippage=slippage,
                running_equity=equity,
                drawdown=drawdown,
                timestamp=timestamp,
                fill_id=fill_id,
            )
            self._pnl_ledger.append(pnl_row)
            return position, pnl_row, self.snapshot(timestamp)

    def apply_close(
        self,
        open_position: PositionLedgerEntry,
        *,
        trade_id: str,
        fill_id: str,
        fill_price: float,
        commission: float,
        slippage: float,
        timestamp: UTCDateTime,
    ) -> tuple[PositionLedgerEntry, PnLLedgerEntry, PaperPortfolioState]:
        """Close an open position and realize PnL."""
        qty = open_position.quantity
        with self._lock:
            if open_position.side == PaperOrderSide.BUY:
                realized = (fill_price - open_position.entry_price) * qty - commission
                self._cash += qty * fill_price - commission
            else:
                realized = (open_position.entry_price - fill_price) * qty - commission
                self._cash -= qty * fill_price + commission

            closed = PositionLedgerEntry(
                position_id=open_position.position_id,
                symbol=open_position.symbol,
                market=open_position.market,
                side=open_position.side,
                quantity=qty,
                entry_price=open_position.entry_price,
                fill_price=fill_price,
                status=PositionStatus.CLOSED,
                opened_at=open_position.opened_at,
                closed_at=timestamp,
                fill_id=fill_id,
                trade_id=trade_id,
            )
            self._position_ledger.append(closed)
            equity = self._compute_equity()
            self._peak_equity = max(self._peak_equity, equity)
            drawdown = max(0.0, self._peak_equity - equity)
            pnl_row = PnLLedgerEntry(
                trade_id=trade_id,
                position_id=open_position.position_id,
                symbol=open_position.symbol,
                market=open_position.market,
                realized_pnl=realized,
                unrealized_pnl=0.0,
                commission=commission,
                slippage=slippage,
                running_equity=equity,
                drawdown=drawdown,
                timestamp=timestamp,
                fill_id=fill_id,
            )
            self._pnl_ledger.append(pnl_row)
            return closed, pnl_row, self.snapshot(timestamp)

    def snapshot(self, timestamp: UTCDateTime) -> PaperPortfolioState:
        with self._lock:
            open_rows = tuple(
                e for e in self._position_ledger.entries() if e.status == PositionStatus.OPEN
            )
            closed_rows = tuple(
                e for e in self._position_ledger.entries() if e.status == PositionStatus.CLOSED
            )
            equity = self._compute_equity()
            margin_used = sum(p.quantity * p.fill_price for p in open_rows)
            return PaperPortfolioState(
                cash=self._cash,
                equity=equity,
                margin_used=margin_used,
                free_margin=equity - margin_used,
                open_positions=open_rows,
                closed_positions=closed_rows,
                peak_equity=self._peak_equity,
                updated_at=timestamp,
            )

    def _compute_equity(self) -> float:
        open_rows = [e for e in self._position_ledger.entries() if e.status == PositionStatus.OPEN]
        unrealized_notional = sum(p.quantity * p.fill_price for p in open_rows)
        return self._cash + unrealized_notional
