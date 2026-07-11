"""Architecture boundaries for signal_engine."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, PIPELINE_PACKAGES, PipelineLayer


@pytest.mark.architecture
def test_signal_engine_pipeline_layer() -> None:
    assert PIPELINE_PACKAGES["signal_engine"] == PipelineLayer.SIGNAL_ENGINE
    assert PipelineLayer.SIGNAL_ENGINE > PipelineLayer.RISK
    assert PipelineLayer.EXECUTION > PipelineLayer.SIGNAL_ENGINE


@pytest.mark.architecture
def test_signal_engine_forbidden_imports() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["signal_engine"]
    assert "execution" in forbidden
    assert "connectors" in forbidden
    assert "research" in forbidden
    assert "paper_trading" in forbidden
    assert "risk" not in forbidden
