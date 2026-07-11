"""Rules package exports."""

from __future__ import annotations

from signal_engine.exceptions import SignalRuleError
from signal_engine.rules.apply import apply_candidate
from signal_engine.rules.base import CandidateRule
from signal_engine.rules.rsi_macd_rule import RSIMACDRule, closes_from_frames

__all__ = [
    "CandidateRule",
    "RSIMACDRule",
    "SignalRuleError",
    "apply_candidate",
    "closes_from_frames",
]
