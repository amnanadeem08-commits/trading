"""Unit tests for paper risk gate (PAPER-003)."""

from __future__ import annotations

import pytest

from models.risk import RiskVerdictStatus
from paper_trading import (
    PaperRiskRejectedError,
    PaperSessionStatus,
    PaperTradingOrchestrator,
    approval_blocks_fill,
    build_paper_risk_verdict,
    evaluate_paper_risk_gate,
    reset_paper_registry,
    trading_decision_from_signal,
)
from risk.engine.risk_result import RiskResult
from risk.engine.risk_state import RiskState
from risk.scoring.approval_score import ApprovalScore
from signal_engine import SignalAssembler
from tests.signal_helpers import make_assembly_request


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_paper_registry()
    yield
    reset_paper_registry()


def _signal():
    return SignalAssembler().assemble(make_assembly_request(signal_id="sig-risk-1"))


@pytest.mark.unit
def test_fail_closed_when_no_verdict_or_result() -> None:
    signal = _signal()
    gate = evaluate_paper_risk_gate(signal)
    assert gate.passed is False
    assert gate.blocks_fill is True
    assert "missing_risk_verdict_and_result" in gate.reasons


@pytest.mark.unit
def test_verdict_reject_blocks_fill_with_reason() -> None:
    signal = _signal()
    verdict = build_paper_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="daily_loss_limit",
    )
    gate = evaluate_paper_risk_gate(signal, verdict=verdict)
    assert gate.passed is False
    assert gate.reasons == ("daily_loss_limit",)


@pytest.mark.unit
def test_verdict_approve_allows_continuation() -> None:
    signal = _signal()
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED)
    gate = evaluate_paper_risk_gate(signal, verdict=verdict)
    assert gate.passed is True
    assert gate.blocks_fill is False
    assert "profit guarantee" in gate.message.lower() or "not a profit" in gate.message.lower()


@pytest.mark.unit
def test_risk_result_reject_and_failed_block() -> None:
    signal = _signal()
    rejected = RiskResult(
        risk_id="r1",
        engine_id="e1",
        state=RiskState.REJECTED,
        metadata={"reason": "policy_non_compliant"},
        output={"rejected": True, "reason": "policy_non_compliant"},
    )
    gate = evaluate_paper_risk_gate(signal, risk_result=rejected)
    assert gate.passed is False
    assert "policy_non_compliant" in gate.reasons

    failed = RiskResult(risk_id="r2", engine_id="e1", state=RiskState.FAILED)
    gate_failed = evaluate_paper_risk_gate(signal, risk_result=failed)
    assert gate_failed.passed is False


@pytest.mark.unit
def test_approval_score_false_blocks() -> None:
    signal = _signal()
    result = RiskResult(
        risk_id="r3",
        engine_id="e1",
        state=RiskState.APPROVED,
        approval=ApprovalScore(value=0.0, approved=False),
    )
    gate = evaluate_paper_risk_gate(signal, risk_result=result)
    assert gate.passed is False
    assert approval_blocks_fill(ApprovalScore(value=0.1, approved=False)) is True


@pytest.mark.unit
def test_authorize_fill_raises_on_reject() -> None:
    orchestrator = PaperTradingOrchestrator()
    signal = _signal()
    verdict = build_paper_risk_verdict(
        signal,
        status=RiskVerdictStatus.REJECTED,
        rejection_reason="exposure_cap",
    )
    with pytest.raises(PaperRiskRejectedError) as exc:
        orchestrator.authorize_fill(signal, verdict=verdict)
    assert "exposure_cap" in exc.value.reasons


@pytest.mark.unit
def test_authorize_fill_passes_on_approve() -> None:
    orchestrator = PaperTradingOrchestrator()
    signal = _signal()
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED)
    gate = orchestrator.authorize_fill(signal, verdict=verdict)
    assert gate.passed is True


@pytest.mark.unit
def test_prepare_with_risk_gate_registers_reject_and_approve() -> None:
    orchestrator = PaperTradingOrchestrator()
    signal = _signal()
    rejected = orchestrator.prepare_with_risk_gate(
        signal,
        session_id="ps-rej",
        verdict=build_paper_risk_verdict(
            signal,
            status=RiskVerdictStatus.REJECTED,
            rejection_reason="margin_breach",
        ),
    )
    assert rejected.status == PaperSessionStatus.RISK_REJECTED
    assert rejected.risk_gate_reasons == ("margin_breach",)
    assert orchestrator.get_session("ps-rej").status == PaperSessionStatus.RISK_REJECTED

    approved = orchestrator.prepare_with_risk_gate(
        signal,
        session_id="ps-ok",
        verdict=build_paper_risk_verdict(signal, status=RiskVerdictStatus.APPROVED),
    )
    assert approved.status == PaperSessionStatus.RISK_APPROVED
    assert approved.risk_gate_reasons == ()


@pytest.mark.unit
def test_rejected_verdict_requires_reason() -> None:
    signal = _signal()
    with pytest.raises(ValueError, match="rejection_reason"):
        build_paper_risk_verdict(signal, status=RiskVerdictStatus.REJECTED)


@pytest.mark.unit
def test_modified_verdict_allows_continuation() -> None:
    signal = _signal()
    verdict = build_paper_risk_verdict(signal, status=RiskVerdictStatus.MODIFIED)
    gate = evaluate_paper_risk_gate(signal, verdict=verdict)
    assert gate.passed is True


@pytest.mark.unit
def test_processing_risk_result_fail_closed() -> None:
    signal = _signal()
    result = RiskResult(
        risk_id="r-proc",
        engine_id="e1",
        state=RiskState.PROCESSING,
    )
    gate = evaluate_paper_risk_gate(signal, risk_result=result)
    assert gate.passed is False


@pytest.mark.unit
def test_trading_decision_from_signal() -> None:
    signal = _signal()
    decision = trading_decision_from_signal(signal)
    assert decision.symbol_id == signal.symbol_id
    assert decision.state == signal.decision
