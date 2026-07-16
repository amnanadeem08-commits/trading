"""Execute deterministic fills and update ledgers (PAPER-004)."""

from __future__ import annotations

import hashlib

from models.common import UTCDateTime, utc_now
from models.decision import DecisionState
from paper_trading.contracts.fill import FillConfig, SimulatedFill
from paper_trading.contracts.ledger import PnLLedgerEntry, PositionLedgerEntry
from paper_trading.contracts.paper_order import PaperOrderRequest, PaperOrderSide
from paper_trading.contracts.portfolio import PaperPortfolioState
from paper_trading.exceptions import PaperOrchestrationError
from paper_trading.fill.engine import compute_commission, compute_fill_price
from paper_trading.ledger.position_ledger import PositionLedger
from paper_trading.portfolio.manager import PaperPortfolioManager


def _deterministic_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}-{digest}"


class FillExecutionResult:
    """Outcome of a simulated fill execution."""

    __slots__ = (
        "closed_position",
        "fill",
        "pnl_entry",
        "portfolio",
        "position_entry",
    )

    def __init__(
        self,
        *,
        fill: SimulatedFill,
        position_entry: PositionLedgerEntry,
        pnl_entry: PnLLedgerEntry,
        portfolio: PaperPortfolioState,
        closed_position: PositionLedgerEntry | None = None,
    ) -> None:
        self.fill = fill
        self.position_entry = position_entry
        self.pnl_entry = pnl_entry
        self.portfolio = portfolio
        self.closed_position = closed_position


class SimulatedFillExecutor:
    """Deterministic fill executor — no live brokers, no randomness."""

    def __init__(
        self,
        *,
        config: FillConfig | None = None,
        portfolio_manager: PaperPortfolioManager | None = None,
        position_ledger: PositionLedger | None = None,
    ) -> None:
        self._config = config or FillConfig()
        if portfolio_manager is not None:
            self._portfolio = portfolio_manager
        else:
            self._portfolio = PaperPortfolioManager(
                config=self._config,
                position_ledger=position_ledger,
            )

    @property
    def config(self) -> FillConfig:
        return self._config

    @property
    def portfolio_manager(self) -> PaperPortfolioManager:
        return self._portfolio

    def execute(
        self,
        order: PaperOrderRequest,
        *,
        timestamp: UTCDateTime | None = None,
        fill_fraction: float | None = None,
    ) -> FillExecutionResult:
        """Execute a deterministic simulated fill for a mapped paper order."""
        if order.side == PaperOrderSide.FLAT or order.decision == DecisionState.HOLD:
            raise PaperOrchestrationError("Cannot fill FLAT/HOLD orders")
        if order.reference_price is None or order.reference_price <= 0:
            raise PaperOrchestrationError("reference_price required for simulated fill")

        ts = timestamp or utc_now()
        qty = order.quantity if order.quantity is not None else self._config.default_quantity
        fraction = fill_fraction if fill_fraction is not None else self._config.fill_fraction
        filled_qty = qty * fraction
        if filled_qty <= 0:
            raise PaperOrchestrationError("filled quantity must be > 0")

        fill_price, spread_amt, slippage_amt = compute_fill_price(
            order.reference_price,
            order.side,
            config=self._config,
        )
        notional = filled_qty * fill_price
        commission = compute_commission(notional, self._config.commission_bps)
        id_seed = (
            f"{order.request_id}|{order.session_id}|{ts.isoformat()}|{filled_qty}|{fill_price}"
        )
        fill_id = _deterministic_id("fill", id_seed)
        trade_id = _deterministic_id("trade", id_seed)
        position_id = _deterministic_id("pos", id_seed)

        fill = SimulatedFill(
            fill_id=fill_id,
            trade_id=trade_id,
            session_id=order.session_id,
            request_id=order.request_id,
            signal_id=order.signal_id,
            symbol_id=order.symbol_id,
            market_id=order.market_id,
            side=order.side,
            quantity=filled_qty,
            reference_price=order.reference_price,
            fill_price=fill_price,
            slippage=slippage_amt * filled_qty,
            commission=commission,
            spread=spread_amt * filled_qty,
            notional=notional,
            filled_at=ts,
        )

        existing = self._portfolio.position_ledger.open_for_symbol(order.symbol_id)
        closed_position: PositionLedgerEntry | None = None

        if (
            order.side == PaperOrderSide.SELL
            and existing is not None
            and existing.side == PaperOrderSide.BUY
        ):
            closed, pnl_row, portfolio = self._portfolio.apply_close(
                existing,
                trade_id=trade_id,
                fill_id=fill_id,
                fill_price=fill_price,
                commission=commission,
                slippage=slippage_amt * filled_qty,
                timestamp=ts,
            )
            closed_position = closed
            return FillExecutionResult(
                fill=fill,
                position_entry=closed,
                pnl_entry=pnl_row,
                portfolio=portfolio,
                closed_position=closed,
            )

        position, pnl_row, portfolio = self._portfolio.apply_open(
            position_id=position_id,
            trade_id=trade_id,
            fill_id=fill_id,
            symbol=order.symbol_id,
            market=order.market_id,
            side=order.side,
            quantity=filled_qty,
            entry_price=order.reference_price,
            fill_price=fill_price,
            commission=commission,
            slippage=slippage_amt * filled_qty,
            timestamp=ts,
        )
        return FillExecutionResult(
            fill=fill,
            position_entry=position,
            pnl_entry=pnl_row,
            portfolio=portfolio,
            closed_position=closed_position,
        )
