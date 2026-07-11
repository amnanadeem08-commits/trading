"""Risk gate binder for paper trading (fail closed before simulated fill).

Uses foundation ``RiskVerdict`` / ``RiskResult`` contracts. Does **not** place
fills (PAPER-004). An approved gate is not a profit-protection guarantee.
"""

from __future__ import annotations

from models.decision import TradingDecision
from models.risk import RiskAssessment, RiskVerdict, RiskVerdictStatus
from models.signal import ExplainableSignal
from paper_trading.contracts.paper_risk import PaperRiskGateResult
from risk.engine.risk_result import RiskResult
from risk.engine.risk_state import RiskState
from risk.scoring.approval_score import ApprovalScore

_DISCLAIMER = (
    "Risk gate approval authorizes continuation only; it is not a profit "
    "guarantee and does not imply loss protection."
)


def trading_decision_from_signal(signal: ExplainableSignal) -> TradingDecision:
    """Build a ``TradingDecision`` snapshot from an explainable signal."""
    return TradingDecision(
        decision_id=f"td-{signal.signal_id}",
        symbol_id=signal.symbol_id,
        market_id=signal.market_id,
        state=signal.decision,
        source=signal.decision_source,
        confidence=signal.confidence,
        strategy_id=signal.provenance.strategy_version,
        strategy_version=signal.provenance.strategy_version,
        reproducibility=signal.reproducibility,
        rationale=(
            signal.llm_insight.reasoning
            if signal.llm_insight is not None and signal.llm_insight.reasoning.strip()
            else f"Paper risk gate decision snapshot for {signal.signal_id}"
        ),
    )


def build_paper_risk_verdict(
    signal: ExplainableSignal,
    *,
    status: RiskVerdictStatus,
    verdict_id: str | None = None,
    rejection_reason: str | None = None,
    assessment: RiskAssessment | None = None,
    modified_decision: TradingDecision | None = None,
) -> RiskVerdict:
    """Construct a ``RiskVerdict`` bound to the signal's decision/assessment."""
    decision = trading_decision_from_signal(signal)
    reasons_ok = status != RiskVerdictStatus.REJECTED or (
        rejection_reason is not None and rejection_reason.strip() != ""
    )
    if not reasons_ok:
        msg = "REJECTED RiskVerdict requires a non-empty rejection_reason"
        raise ValueError(msg)
    return RiskVerdict(
        verdict_id=verdict_id or f"rv-{signal.signal_id}",
        decision=decision,
        status=status,
        modified_decision=modified_decision,
        assessment=assessment if assessment is not None else signal.risk_assessment,
        rejection_reason=rejection_reason,
    )


def _reasons_from_risk_result(result: RiskResult) -> tuple[str, ...]:
    reasons: list[str] = []
    meta_reason = result.metadata.get("reason")
    if meta_reason:
        reasons.append(str(meta_reason))
    output_reason = result.output.get("reason")
    if output_reason and str(output_reason) not in reasons:
        reasons.append(str(output_reason))
    failed_rules = result.validation.get("failed_rules")
    if isinstance(failed_rules, list):
        for rule in failed_rules:
            text = f"validation_rule:{rule}"
            if text not in reasons:
                reasons.append(text)
    if result.approval is not None and not result.approval.approved:
        reasons.append("approval_score_not_approved")
    if not reasons:
        reasons.append(f"risk_state_{result.state.value}")
    return tuple(reasons)


def evaluate_paper_risk_gate(
    signal: ExplainableSignal,
    *,
    verdict: RiskVerdict | None = None,
    risk_result: RiskResult | None = None,
) -> PaperRiskGateResult:
    """Evaluate whether a simulated fill may continue.

    Fail closed when:
    - neither ``verdict`` nor ``risk_result`` is provided
    - ``RiskVerdict.status`` is REJECTED
    - ``RiskResult.state`` is REJECTED or FAILED
    - ``ApprovalScore.approved`` is False
    """
    _ = signal  # signal identity reserved for future ledger correlation
    if verdict is None and risk_result is None:
        return PaperRiskGateResult(
            passed=False,
            reasons=("missing_risk_verdict_and_result",),
            verdict=None,
            risk_result=None,
            message=(
                "Fail closed: no RiskVerdict or RiskResult supplied; " "simulated fill is blocked"
            ),
        )

    if verdict is not None and verdict.status == RiskVerdictStatus.REJECTED:
        reason = (verdict.rejection_reason or "").strip() or "risk_verdict_rejected"
        return PaperRiskGateResult(
            passed=False,
            reasons=(reason,),
            verdict=verdict,
            risk_result=risk_result,
            message=f"Risk verdict REJECTED; simulated fill blocked ({reason})",
        )

    if risk_result is not None:
        if risk_result.state in {RiskState.REJECTED, RiskState.FAILED}:
            reasons = _reasons_from_risk_result(risk_result)
            return PaperRiskGateResult(
                passed=False,
                reasons=reasons,
                verdict=verdict,
                risk_result=risk_result,
                message=(
                    f"RiskResult state={risk_result.state.value}; "
                    f"simulated fill blocked ({'; '.join(reasons)})"
                ),
            )
        if risk_result.approval is not None and not risk_result.approval.approved:
            return PaperRiskGateResult(
                passed=False,
                reasons=("approval_score_not_approved",),
                verdict=verdict,
                risk_result=risk_result,
                message="ApprovalScore.approved is False; simulated fill blocked",
            )
        if risk_result.state not in {RiskState.APPROVED}:
            return PaperRiskGateResult(
                passed=False,
                reasons=(f"non_terminal_or_unapproved_state:{risk_result.state.value}",),
                verdict=verdict,
                risk_result=risk_result,
                message=(
                    f"Fail closed: RiskResult state={risk_result.state.value} "
                    "does not authorize fill"
                ),
            )

    if verdict is not None and verdict.status == RiskVerdictStatus.MODIFIED:
        return PaperRiskGateResult(
            passed=True,
            reasons=(),
            verdict=verdict,
            risk_result=risk_result,
            message=(
                "Risk verdict MODIFIED; continuation allowed with modified decision. " + _DISCLAIMER
            ),
        )

    return PaperRiskGateResult(
        passed=True,
        reasons=(),
        verdict=verdict,
        risk_result=risk_result,
        message="Risk gate approved; continuation allowed. " + _DISCLAIMER,
    )


def approval_blocks_fill(approval: ApprovalScore) -> bool:
    """True when an approval score must block simulated fill."""
    return not approval.approved
