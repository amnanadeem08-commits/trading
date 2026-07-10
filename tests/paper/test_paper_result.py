"""Unit tests for paper execution result."""

from __future__ import annotations

import pytest

from connectors import PaperExecutionResult, PaperState
from models.common import utc_now


def test_paper_execution_result_defaults() -> None:
    result = PaperExecutionResult(
        execution_id="exec-1",
        request_id="req-1",
    )
    assert result.status == PaperState.COMPLETED
    assert result.validation_passed is True
    assert result.latency_ms == 0


def test_paper_execution_result_fields() -> None:
    started = utc_now()
    completed = utc_now()
    result = PaperExecutionResult(
        execution_id="exec-2",
        request_id="req-2",
        status=PaperState.FAILED,
        latency_ms=12,
        duration_ms=20,
        metadata={"mode": "simulation"},
        validation_passed=False,
        started_at=started,
        completed_at=completed,
        synthetic_fill={"filled": False},
    )
    assert result.status == PaperState.FAILED
    assert result.metadata["mode"] == "simulation"
    assert result.synthetic_fill["filled"] is False


def test_paper_execution_result_requires_ids() -> None:
    with pytest.raises(ValueError):
        PaperExecutionResult(execution_id="", request_id="req-1")
