"""Build auditable backtest reports from runner output."""

from __future__ import annotations

from backtesting.contracts.config import BacktestConfig
from backtesting.contracts.report import (
    BacktestReport,
    BacktestRiskConfigReference,
    BacktestSimulationConfigReference,
    BacktestStrategyConfigReference,
)
from backtesting.contracts.request import BacktestRequest
from backtesting.contracts.run import BacktestRunResult
from backtesting.contracts.trade import BacktestTradeLifecycle


def _config_references(
    *,
    strategy_version: str,
    config: BacktestConfig,
) -> tuple[
    BacktestStrategyConfigReference,
    BacktestRiskConfigReference,
    BacktestSimulationConfigReference,
]:
    strategy = BacktestStrategyConfigReference(
        strategy_version=strategy_version,
        min_bars_for_signal=config.min_bars_for_signal,
        seed=config.seed,
    )
    risk = BacktestRiskConfigReference(
        require_risk_approval=config.require_risk_approval,
        stop_loss_pct=config.stop_loss_pct,
        take_profit_pct=config.take_profit_pct,
    )
    simulation = BacktestSimulationConfigReference(
        slippage_bps=config.slippage_bps,
        commission_bps=config.commission_bps,
        spread_bps=config.spread_bps,
        initial_cash=config.initial_cash,
        default_quantity=config.default_quantity,
    )
    return strategy, risk, simulation


def _default_warnings(*, rejected_count: int) -> tuple[str, ...]:
    warnings: list[str] = []
    if rejected_count > 0:
        warnings.append(
            f"{rejected_count} signal(s) rejected by risk gate; see rejected_trades for audit."
        )
    return tuple(warnings)


def _default_technical_notes() -> tuple[str, ...]:
    return (
        "TD-BT-01: fill pricing uses local backtesting adapter (no paper_trading import).",
        "TD-BT-02: backtesting assumes full fill (fill_fraction=1.0); paper may differ.",
        "Results are simulated historical replays for research only — not financial advice.",
    )


def build_backtest_report(
    result: BacktestRunResult,
    *,
    request: BacktestRequest | None = None,
    warnings: tuple[str, ...] | None = None,
    technical_notes: tuple[str, ...] | None = None,
) -> BacktestReport:
    """Materialize a stable report boundary from a completed run result."""
    config = request.config if request is not None else BacktestConfig()
    strategy_version = (
        request.strategy_version if request is not None else result.strategy_version
    )
    strategy_ref, risk_ref, simulation_ref = _config_references(
        strategy_version=strategy_version,
        config=config,
    )

    rejected = tuple(
        trade for trade in result.trades if trade.lifecycle == BacktestTradeLifecycle.REJECTED
    )
    closed = tuple(
        trade for trade in result.trades if trade.lifecycle != BacktestTradeLifecycle.REJECTED
    )

    report_warnings = warnings if warnings is not None else _default_warnings(
        rejected_count=len(rejected)
    )
    report_notes = (
        technical_notes if technical_notes is not None else _default_technical_notes()
    )

    return BacktestReport(
        run_id=result.run_id,
        symbol_id=result.symbol_id,
        market_id=result.market_id,
        timeframe=result.timeframe,
        started_at=result.started_at,
        completed_at=result.completed_at,
        candles_processed=result.summary.candles_processed,
        strategy_config=strategy_ref,
        risk_config=risk_ref,
        simulation_config=simulation_ref,
        trades=closed,
        rejected_trades=rejected,
        summary=result.summary,
        warnings=report_warnings,
        technical_notes=report_notes,
        deterministic=result.deterministic,
    )
