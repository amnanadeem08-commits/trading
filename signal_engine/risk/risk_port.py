"""Risk / invalidation / confidence provider port."""

from __future__ import annotations

from typing import Protocol

from models.decision import DecisionState
from models.risk import RiskAssessment
from models.signal import InvalidationRule
from risk.scoring.confidence_score import ConfidenceScore


class RiskBindingProvider(Protocol):
    """Port that produces confidence, risk assessment, and invalidation bindings."""

    def get_confidence(
        self,
        *,
        symbol_id: str,
        decision: DecisionState,
        indicator_values: dict[str, float | str | int | bool],
    ) -> ConfidenceScore:
        """Return a confidence score (not a probability of profit)."""

    def get_assessment(
        self,
        *,
        symbol_id: str,
        decision: DecisionState,
        confidence: float,
        indicator_values: dict[str, float | str | int | bool],
    ) -> RiskAssessment:
        """Return a risk assessment narrative for the signal."""

    def get_invalidation(
        self,
        *,
        decision: DecisionState,
        indicator_values: dict[str, float | str | int | bool],
    ) -> InvalidationRule:
        """Return an invalidation rule for the signal thesis."""
