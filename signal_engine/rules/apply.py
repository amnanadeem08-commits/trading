"""Helpers to apply candidates onto assembly requests."""

from __future__ import annotations

from signal_engine.candidates.candidate import DirectionCandidate
from signal_engine.contracts.assembly_request import SignalAssemblyRequest


def apply_candidate(
    request: SignalAssemblyRequest,
    candidate: DirectionCandidate,
) -> SignalAssemblyRequest:
    """Return a copy of the request with candidate decision/indicator fields applied."""
    return request.model_copy(
        update={
            "decision": candidate.decision,
            "decision_source": candidate.decision_source,
            "confidence": candidate.confidence,
            "indicators_used": candidate.indicators_used,
            "indicator_values": candidate.indicator_values,
            "alternative_scenario": candidate.rationale,
        }
    )
