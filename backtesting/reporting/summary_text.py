"""Human-readable backtest summary formatting."""

from __future__ import annotations

from backtesting.contracts.report import BacktestReport


def _fmt_optional(value: float | None, *, suffix: str = "", precision: int = 2) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{precision}f}{suffix}"


def _fmt_win_rate(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def format_backtest_summary_text(report: BacktestReport) -> str:
    """Render a concise human-readable summary for logs or review."""
    summary = report.summary
    lines = [
        f"Backtest Report [{report.run_id}]",
        (
            f"Symbol: {report.symbol_id} | Market: {report.market_id} | "
            f"Timeframe: {report.timeframe}"
        ),
        (
            f"Period: {report.started_at.isoformat()} → {report.completed_at.isoformat()} | "
            f"Candles: {report.candles_processed}"
        ),
        (
            f"Strategy: {report.strategy_config.strategy_version} "
            f"(seed={report.strategy_config.seed}, "
            f"min_bars={report.strategy_config.min_bars_for_signal})"
        ),
        (
            f"Risk: stop={report.risk_config.stop_loss_pct:.2%}, "
            f"target={report.risk_config.take_profit_pct:.2%}, "
            f"approval_required={report.risk_config.require_risk_approval}"
        ),
        (
            f"Trades: {summary.total_trades} "
            f"({summary.wins}W/{summary.losses}L/{summary.breakeven_trades}BE) | "
            f"Rejected: {summary.rejected_trades}"
        ),
        (
            f"Win rate: {_fmt_win_rate(summary.win_rate)} | "
            f"Gross P&L: {summary.gross_pnl:.2f} | Net P&L: {summary.net_pnl:.2f} | "
            f"Fees: {summary.total_fees:.2f}"
        ),
        (
            f"Avg return: {_fmt_optional(summary.average_return_pct, suffix='%')} | "
            f"Profit factor: {_fmt_optional(summary.profit_factor)} | "
            f"Max drawdown: {_fmt_optional(summary.max_drawdown)} | "
            f"Avg R/R: {_fmt_optional(summary.average_risk_reward)}"
        ),
        f"Final equity: {summary.final_equity:.2f}",
    ]
    if report.warnings:
        lines.append("Warnings:")
        lines.extend(f"  - {warning}" for warning in report.warnings)
    if report.technical_notes:
        lines.append("Notes:")
        lines.extend(f"  - {note}" for note in report.technical_notes)
    lines.append(
        "Disclaimer: simulated historical replay for research only — not financial advice."
    )
    return "\n".join(lines)
