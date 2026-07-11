"""Architecture boundaries for paper_trading."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, PIPELINE_PACKAGES, PipelineLayer


@pytest.mark.architecture
def test_paper_trading_pipeline_layer() -> None:
    assert PIPELINE_PACKAGES["paper_trading"] == PipelineLayer.PAPER_TRADING
    assert PipelineLayer.PAPER_TRADING > PipelineLayer.EXECUTION
    assert PipelineLayer.PAPER_TRADING > PipelineLayer.SIGNAL_ENGINE


@pytest.mark.architecture
def test_paper_trading_forbidden_imports() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["paper_trading"]
    assert "api" in forbidden
    assert "dashboard" in forbidden
    assert "research" in forbidden
    assert "connectors" not in forbidden
    assert "signal_engine" not in forbidden
    assert "risk" not in forbidden


@pytest.mark.architecture
def test_paper_trading_may_import_risk_contracts() -> None:
    """PAPER-003 binder uses foundation risk contracts without reverse imports."""
    from paper_trading.risk import evaluate_paper_risk_gate
    from risk.engine.risk_result import RiskResult
    from risk.engine.risk_state import RiskState

    assert callable(evaluate_paper_risk_gate)
    assert RiskState.REJECTED.value == "rejected"
    assert RiskResult.__name__ == "RiskResult"
