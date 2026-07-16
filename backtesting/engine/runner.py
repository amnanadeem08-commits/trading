"""Deterministic backtest runner."""

from __future__ import annotations

from dataclasses import dataclass

from backtesting.contracts.request import BacktestRequest
from backtesting.contracts.run import BacktestRunResult
from backtesting.contracts.trade import (
    BacktestTradeLifecycle,
    BacktestTradeOutcome,
    BacktestTradeResult,
)
from backtesting.engine.candle_feed import ChronologicalCandleFeed
from backtesting.engine.ids import resolve_run_id, trade_id_for_bar
from backtesting.engine.metrics import compute_backtest_summary
from backtesting.engine.position import OpenBacktestPosition
from backtesting.engine.pricing import compute_commission, compute_fill_price
from backtesting.engine.risk_evaluator import evaluate_backtest_risk, resolve_backtest_risk_verdict
from backtesting.engine.signal_evaluator import evaluate_signal_at_bar
from backtesting.exceptions import BacktestConfigurationError
from market_data.models.candle import Candle
from models.common import UTCDateTime
from models.decision import DecisionState
from models.risk import RiskVerdictStatus
from models.signal import ExplainableSignal


@dataclass(frozen=True, slots=True)
class _ExitDecision:
    price: float
    reason: str
    lifecycle: BacktestTradeLifecycle


def _stop_target_prices(
    *,
    direction: DecisionState,
    entry_price: float,
    stop_loss_pct: float,
    take_profit_pct: float,
) -> tuple[float, float]:
    if direction == DecisionState.BUY:
        stop = entry_price * (1.0 - stop_loss_pct)
        target = entry_price * (1.0 + take_profit_pct)
    elif direction == DecisionState.SELL:
        stop = entry_price * (1.0 + stop_loss_pct)
        target = entry_price * (1.0 - take_profit_pct)
    else:
        msg = f"Unsupported direction for stop/target: {direction}"
        raise BacktestConfigurationError(msg)
    return stop, target


def _check_exit(position: OpenBacktestPosition, candle: Candle) -> _ExitDecision | None:
    if position.direction == DecisionState.BUY:
        if candle.low <= position.stop_price:
            return _ExitDecision(
                price=position.stop_price,
                reason="stop_loss",
                lifecycle=BacktestTradeLifecycle.STOP_LOSS,
            )
        if position.invalidation_price is not None and candle.low <= position.invalidation_price:
            return _ExitDecision(
                price=position.invalidation_price,
                reason="signal_exit",
                lifecycle=BacktestTradeLifecycle.SIGNAL_EXIT,
            )
        if candle.high >= position.target_price:
            return _ExitDecision(
                price=position.target_price,
                reason="take_profit",
                lifecycle=BacktestTradeLifecycle.TAKE_PROFIT,
            )
    elif position.direction == DecisionState.SELL:
        if candle.high >= position.stop_price:
            return _ExitDecision(
                price=position.stop_price,
                reason="stop_loss",
                lifecycle=BacktestTradeLifecycle.STOP_LOSS,
            )
        if position.invalidation_price is not None and candle.high >= position.invalidation_price:
            return _ExitDecision(
                price=position.invalidation_price,
                reason="signal_exit",
                lifecycle=BacktestTradeLifecycle.SIGNAL_EXIT,
            )
        if candle.low <= position.target_price:
            return _ExitDecision(
                price=position.target_price,
                reason="take_profit",
                lifecycle=BacktestTradeLifecycle.TAKE_PROFIT,
            )
    return None


def _gross_pnl(
    *,
    direction: DecisionState,
    entry_price: float,
    exit_price: float,
    quantity: float,
) -> float:
    if direction == DecisionState.BUY:
        return (exit_price - entry_price) * quantity
    return (entry_price - exit_price) * quantity


def _return_pct(*, net_pnl: float, entry_price: float, quantity: float) -> float | None:
    notional = entry_price * quantity
    if notional <= 0:
        return None
    return net_pnl / notional * 100.0


def _outcome_from_pnl(net_pnl: float) -> BacktestTradeOutcome:
    if net_pnl > 0:
        return BacktestTradeOutcome.WIN
    if net_pnl < 0:
        return BacktestTradeOutcome.LOSS
    return BacktestTradeOutcome.BREAKEVEN


def _close_position(
    position: OpenBacktestPosition,
    *,
    run_id: str,
    symbol_id: str,
    market_id: str,
    timeframe: str,
    exit_price: float,
    exit_at: UTCDateTime,
    exit_bar_index: int,
    exit_reason: str,
    lifecycle: BacktestTradeLifecycle,
    risk_verdict_status: RiskVerdictStatus,
    spread_bps: float,
    slippage_bps: float,
    commission_bps: float,
) -> BacktestTradeResult:
    exit_fill, _, exit_slippage_amt = compute_fill_price(
        exit_price,
        position.direction,
        spread_bps=spread_bps,
        slippage_bps=slippage_bps,
    )
    exit_notional = exit_fill * position.quantity
    exit_commission = compute_commission(exit_notional, commission_bps)
    exit_slippage = exit_slippage_amt * position.quantity
    exit_fees = exit_commission + exit_slippage

    gross = _gross_pnl(
        direction=position.direction,
        entry_price=position.entry_price,
        exit_price=exit_fill,
        quantity=position.quantity,
    )
    total_commission = position.commission + exit_commission
    total_slippage = position.slippage + exit_slippage
    total_fees = position.fees + exit_fees
    net = gross - total_fees

    return BacktestTradeResult(
        trade_id=position.trade_id,
        run_id=run_id,
        signal_id=position.signal_id,
        symbol_id=symbol_id,
        market_id=market_id,
        timeframe=timeframe,
        direction=position.direction,
        lifecycle=lifecycle,
        risk_verdict_status=risk_verdict_status,
        entry_price=position.entry_price,
        exit_price=exit_fill,
        stop_price=position.stop_price,
        target_price=position.target_price,
        quantity=position.quantity,
        commission=total_commission,
        slippage=total_slippage,
        fees=total_fees,
        gross_pnl=gross,
        net_pnl=net,
        return_pct=_return_pct(
            net_pnl=net, entry_price=position.entry_price, quantity=position.quantity
        ),
        outcome=_outcome_from_pnl(net),
        entry_at=position.entry_at,
        exit_at=exit_at,
        entry_bar_index=position.entry_bar_index,
        exit_bar_index=exit_bar_index,
        exit_reason=exit_reason,
    )


def _record_rejected_signal(
    signal: ExplainableSignal,
    *,
    run_id: str,
    symbol_id: str,
    market_id: str,
    timeframe: str,
    reference_price: float,
    bar_index: int,
    timestamp: UTCDateTime,
    quantity: float,
    stop_loss_pct: float,
    take_profit_pct: float,
    rejection_reason: str,
    risk_verdict_status: RiskVerdictStatus,
) -> BacktestTradeResult:
    stop, target = _stop_target_prices(
        direction=signal.decision,
        entry_price=reference_price,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
    )
    trade_id = trade_id_for_bar(
        run_id=run_id,
        bar_index=bar_index,
        direction=signal.decision.value,
        timestamp_iso=timestamp.isoformat(),
    )
    return BacktestTradeResult(
        trade_id=trade_id,
        run_id=run_id,
        signal_id=signal.signal_id,
        symbol_id=symbol_id,
        market_id=market_id,
        timeframe=timeframe,
        direction=signal.decision,
        lifecycle=BacktestTradeLifecycle.REJECTED,
        risk_verdict_status=risk_verdict_status,
        risk_rejection_reason=rejection_reason,
        entry_price=reference_price,
        exit_price=None,
        stop_price=stop,
        target_price=target,
        quantity=quantity,
        outcome=BacktestTradeOutcome.REJECTED,
        entry_at=timestamp,
        entry_bar_index=bar_index,
        exit_reason="risk_rejected",
    )


def _invalidation_price(signal: ExplainableSignal) -> float | None:
    level = signal.invalidation.price_level
    if level is None or level <= 0:
        return None
    return float(level)


def _open_position_from_signal(
    signal: ExplainableSignal,
    *,
    run_id: str,
    symbol_id: str,
    market_id: str,
    timeframe: str,
    reference_price: float,
    bar_index: int,
    timestamp: UTCDateTime,
    quantity: float,
    stop_loss_pct: float,
    take_profit_pct: float,
    spread_bps: float,
    slippage_bps: float,
    commission_bps: float,
    risk_verdict_status: RiskVerdictStatus,
) -> OpenBacktestPosition:
    fill_price, _, slippage_amt = compute_fill_price(
        reference_price,
        signal.decision,
        spread_bps=spread_bps,
        slippage_bps=slippage_bps,
    )
    notional = fill_price * quantity
    commission = compute_commission(notional, commission_bps)
    slippage = slippage_amt * quantity
    fees = commission + slippage
    stop, target = _stop_target_prices(
        direction=signal.decision,
        entry_price=fill_price,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
    )
    trade_id = trade_id_for_bar(
        run_id=run_id,
        bar_index=bar_index,
        direction=signal.decision.value,
        timestamp_iso=timestamp.isoformat(),
    )
    return OpenBacktestPosition(
        trade_id=trade_id,
        signal_id=signal.signal_id,
        direction=signal.decision,
        entry_price=fill_price,
        stop_price=stop,
        target_price=target,
        quantity=quantity,
        commission=commission,
        slippage=slippage,
        fees=fees,
        invalidation_price=_invalidation_price(signal),
        entry_at=timestamp,
        entry_bar_index=bar_index,
        risk_verdict_status=risk_verdict_status,
    )


class BacktestRunner:
    """Replay historical candles through signal and risk boundaries."""

    def run(self, request: BacktestRequest) -> BacktestRunResult:
        config = request.config
        run_id = resolve_run_id(request)
        feed = ChronologicalCandleFeed(request.candles)
        if feed.total < config.min_bars_for_signal:
            msg = f"Need at least {config.min_bars_for_signal} candles; got {feed.total}"
            raise BacktestConfigurationError(msg)

        trades: list[BacktestTradeResult] = []
        recorded_trade_ids: set[str] = set()
        equity_curve: list[float] = [config.initial_cash]
        equity = config.initial_cash
        open_position: OpenBacktestPosition | None = None
        started_at = request.candles[0].timestamp

        def _append_trade(trade: BacktestTradeResult) -> None:
            if trade.trade_id in recorded_trade_ids:
                return
            recorded_trade_ids.add(trade.trade_id)
            trades.append(trade)

        for index in range(feed.total):
            candle = feed.advance_to(index)
            if open_position is not None:
                exit_decision = _check_exit(open_position, candle)
                if exit_decision is not None:
                    closed = _close_position(
                        open_position,
                        run_id=run_id,
                        symbol_id=request.symbol_id,
                        market_id=request.market_id,
                        timeframe=request.timeframe,
                        exit_price=exit_decision.price,
                        exit_at=candle.timestamp,
                        exit_bar_index=index,
                        exit_reason=exit_decision.reason,
                        lifecycle=exit_decision.lifecycle,
                        risk_verdict_status=open_position.risk_verdict_status,
                        spread_bps=config.spread_bps,
                        slippage_bps=config.slippage_bps,
                        commission_bps=config.commission_bps,
                    )
                    _append_trade(closed)
                    equity += closed.net_pnl
                    equity_curve.append(equity)
                    open_position = None

            if open_position is not None:
                continue

            window = feed.history_window()
            if len(window) < config.min_bars_for_signal:
                continue

            signal = evaluate_signal_at_bar(
                window,
                market_id=request.market_id,
                bar_index=index,
                strategy_version=request.strategy_version,
                config_hash=config.seed,
            )
            if signal is None:
                continue

            verdict = resolve_backtest_risk_verdict(signal, bar_index=index, config=config)
            approved, reasons = evaluate_backtest_risk(
                signal,
                verdict=verdict,
                require_approval=config.require_risk_approval,
            )
            if not approved:
                rejected = _record_rejected_signal(
                    signal,
                    run_id=run_id,
                    symbol_id=request.symbol_id,
                    market_id=request.market_id,
                    timeframe=request.timeframe,
                    reference_price=float(candle.close),
                    bar_index=index,
                    timestamp=candle.timestamp,
                    quantity=config.default_quantity,
                    stop_loss_pct=config.stop_loss_pct,
                    take_profit_pct=config.take_profit_pct,
                    rejection_reason=reasons[0] if reasons else "risk_rejected",
                    risk_verdict_status=verdict.status,
                )
                _append_trade(rejected)
                continue

            candidate = _open_position_from_signal(
                signal,
                run_id=run_id,
                symbol_id=request.symbol_id,
                market_id=request.market_id,
                timeframe=request.timeframe,
                reference_price=float(candle.close),
                bar_index=index,
                timestamp=candle.timestamp,
                quantity=config.default_quantity,
                stop_loss_pct=config.stop_loss_pct,
                take_profit_pct=config.take_profit_pct,
                spread_bps=config.spread_bps,
                slippage_bps=config.slippage_bps,
                commission_bps=config.commission_bps,
                risk_verdict_status=verdict.status,
            )
            if candidate.trade_id in recorded_trade_ids:
                continue
            open_position = candidate

        if open_position is not None:
            last = feed.current()
            closed = _close_position(
                open_position,
                run_id=run_id,
                symbol_id=request.symbol_id,
                market_id=request.market_id,
                timeframe=request.timeframe,
                exit_price=float(last.close),
                exit_at=last.timestamp,
                exit_bar_index=feed.current_index,
                exit_reason="end_of_data",
                lifecycle=BacktestTradeLifecycle.END_OF_DATA,
                risk_verdict_status=open_position.risk_verdict_status,
                spread_bps=config.spread_bps,
                slippage_bps=config.slippage_bps,
                commission_bps=config.commission_bps,
            )
            _append_trade(closed)
            equity += closed.net_pnl
            equity_curve.append(equity)

        completed_at = feed.current().timestamp
        summary = compute_backtest_summary(
            tuple(trades),
            candles_processed=feed.total,
            initial_cash=config.initial_cash,
            equity_curve=tuple(equity_curve),
        )
        return BacktestRunResult(
            run_id=run_id,
            symbol_id=request.symbol_id,
            market_id=request.market_id,
            timeframe=request.timeframe,
            strategy_version=request.strategy_version,
            trades=tuple(trades),
            summary=summary,
            started_at=started_at,
            completed_at=completed_at,
        )
