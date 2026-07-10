"""Unit tests for paper lifecycle states."""

from __future__ import annotations

from connectors import TERMINAL_PAPER_STATES, PaperState


def test_paper_state_values() -> None:
    assert PaperState.NEW.value == "new"
    assert PaperState.QUEUED.value == "queued"
    assert PaperState.ACCEPTED.value == "accepted"
    assert PaperState.SIMULATED.value == "simulated"
    assert PaperState.COMPLETED.value == "completed"
    assert PaperState.FAILED.value == "failed"
    assert PaperState.CANCELLED.value == "cancelled"


def test_terminal_paper_states() -> None:
    assert PaperState.COMPLETED in TERMINAL_PAPER_STATES
    assert PaperState.FAILED in TERMINAL_PAPER_STATES
    assert PaperState.CANCELLED in TERMINAL_PAPER_STATES
    assert PaperState.ACCEPTED not in TERMINAL_PAPER_STATES
