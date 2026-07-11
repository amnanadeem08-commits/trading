"""Candidate rule contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from signal_engine.candidates.candidate import DirectionCandidate
from signal_engine.intake.market_intake import MarketIntakeFrame


class CandidateRule(ABC):
    """Deterministic rule that maps market frames to a direction candidate."""

    @abstractmethod
    def evaluate(self, frames: Sequence[MarketIntakeFrame]) -> DirectionCandidate:
        """Evaluate frames and return a directional candidate."""
