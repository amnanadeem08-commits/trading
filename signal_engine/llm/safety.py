"""Safety checks for LLM insight text (no advice / profit guarantees)."""

from __future__ import annotations

from signal_engine.exceptions import SignalLLMAttachmentError

_FORBIDDEN_PHRASES: tuple[str, ...] = (
    "guaranteed profit",
    "guaranteed profits",
    "financial advice",
    "sure win",
    "risk-free",
    "risk free",
    "cannot lose",
    "will definitely",
    "promise of returns",
)


def assert_safe_insight_text(*parts: str) -> None:
    """Reject insight text that claims advice or guaranteed profits."""
    combined = " ".join(parts).lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase in combined:
            raise SignalLLMAttachmentError(f"Insight text contains forbidden framing: {phrase!r}")
