"""LLM insight attachment package exports."""

from __future__ import annotations

from signal_engine.exceptions import SignalLLMAttachmentError
from signal_engine.llm.attach import (
    attach_llm_insight,
    attach_llm_insight_from_provider,
    ensure_llm_insight_present,
)
from signal_engine.llm.insight_mapper import (
    llm_insight_from_llm_response,
    llm_insight_from_parts,
)
from signal_engine.llm.insight_port import LLMInsightProvider
from signal_engine.llm.safety import assert_safe_insight_text
from signal_engine.llm.stub_provider import StubLLMInsightProvider

__all__ = [
    "LLMInsightProvider",
    "SignalLLMAttachmentError",
    "StubLLMInsightProvider",
    "assert_safe_insight_text",
    "attach_llm_insight",
    "attach_llm_insight_from_provider",
    "ensure_llm_insight_present",
    "llm_insight_from_llm_response",
    "llm_insight_from_parts",
]
