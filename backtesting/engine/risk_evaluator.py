"""Backtest risk evaluation using foundation risk contracts."""

from __future__ import annotations

from backtesting.contracts.config import BacktestConfig
from models.decision import DecisionState, TradingDecision
from models.risk import RiskVerdict, RiskVerdictStatus
from models.signal import ExplainableSignal


def build_backtest_risk_verdict(
    signal: ExplainableSignal,
    *,
    status: RiskVerdictStatus = RiskVerdictStatus.APPROVED,
    rejection_reason: str | None = None,
) -> RiskVerdict:
    """Construct a ``RiskVerdict`` for backtest replay."""
    if status == RiskVerdictStatus.REJECTED and not (rejection_reason or "").strip():
        msg = "REJECTED RiskVerdict requires rejection_reason"
        raise ValueError(msg)
    decision = TradingDecision(
        decision_id=f"td-{signal.signal_id}",
        symbol_id=signal.symbol_id,
        market_id=signal.market_id,
        state=signal.decision,
        source=signal.decision_source,
        confidence=signal.confidence,
        strategy_id=signal.provenance.strategy_version,
        strategy_version=signal.provenance.strategy_version,
        reproducibility=signal.reproducibility,
        rationale=f"Backtest risk snapshot for {signal.signal_id}",
    )
    return RiskVerdict(
        verdict_id=f"rv-{signal.signal_id}",
        decision=decision,
        status=status,
        assessment=signal.risk_assessment,
        rejection_reason=rejection_reason,
    )


def resolve_backtest_risk_verdict(
    signal: ExplainableSignal,
    *,
    bar_index: int,
    config: BacktestConfig,
) -> RiskVerdict:
    """Resolve the risk verdict for a signal at a replay bar."""
    if bar_index in config.force_reject_bar_indices:
        return build_backtest_risk_verdict(
            signal,
            status=RiskVerdictStatus.REJECTED,
            rejection_reason="forced_bar_rejection",
        )
    return build_backtest_risk_verdict(signal)


def evaluate_backtest_risk(
    signal: ExplainableSignal,
    *,
    verdict: RiskVerdict | None = None,
    require_approval: bool = True,
) -> tuple[bool, tuple[str, ...]]:
    """Fail-closed risk gate for backtest entries (PAPER-003 compatible semantics)."""
    if not require_approval:
        return True, ()
    if verdict is None:
        return False, ("missing_risk_verdict",)
    if verdict.status == RiskVerdictStatus.REJECTED:
        reason = (verdict.rejection_reason or "").strip() or "risk_verdict_rejected"
        return False, (reason,)
    if signal.decision in {DecisionState.BUY, DecisionState.SELL} and signal.confidence <= 0:
        return False, ("directional_confidence_required",)
    return True, ()
