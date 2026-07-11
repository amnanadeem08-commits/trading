"""LLM insight provider port."""

from __future__ import annotations

from typing import Protocol

from models.prediction import LLMInsight, MLPrediction
from signal_engine.contracts.assembly_request import SignalAssemblyRequest


class LLMInsightProvider(Protocol):
    """Port that produces LLMInsight for AI-enhanced signals."""

    def get_insight(
        self,
        *,
        request: SignalAssemblyRequest,
        prediction: MLPrediction,
    ) -> LLMInsight:
        """Return an insight or raise on failure (never silent None)."""
