"""Map AI/LLM contracts into LLMInsight."""

from __future__ import annotations

from ai.llm.llm_response import LLMResponse
from ai.prompts.prompt import Prompt
from models.common import VersionInfo
from models.prediction import LLMInsight
from signal_engine.exceptions import SignalLLMAttachmentError
from signal_engine.llm.safety import assert_safe_insight_text


def llm_insight_from_parts(
    *,
    reasoning: str,
    alternative_scenario: str,
    fomo_fear_note: str,
    provider: str,
    model_name: str,
    prompt_version: VersionInfo | str,
    ensemble_votes: dict[str, str] | None = None,
) -> LLMInsight:
    """Build LLMInsight with safety validation."""
    assert_safe_insight_text(reasoning, alternative_scenario, fomo_fear_note)
    if not provider.strip() or not model_name.strip():
        raise SignalLLMAttachmentError("provider and model_name must not be empty")
    version = (
        prompt_version
        if isinstance(prompt_version, VersionInfo)
        else VersionInfo(version_id=str(prompt_version))
    )
    if not version.version_id.strip():
        raise SignalLLMAttachmentError("prompt_version must not be empty")
    return LLMInsight(
        reasoning=reasoning.strip(),
        alternative_scenario=alternative_scenario.strip(),
        fomo_fear_note=fomo_fear_note.strip(),
        provider=provider.strip(),
        model_name=model_name.strip(),
        prompt_version=version,
        ensemble_votes=ensemble_votes,
    )


def llm_insight_from_llm_response(
    response: LLMResponse,
    *,
    prompt: Prompt | None = None,
    prompt_version: VersionInfo | str | None = None,
    alternative_scenario: str | None = None,
    fomo_fear_note: str | None = None,
) -> LLMInsight:
    """Map an ai.LLMResponse (+ optional Prompt) into LLMInsight."""
    if not response.content.strip():
        raise SignalLLMAttachmentError("LLM response content is empty")
    version: VersionInfo | str
    if prompt_version is not None:
        version = prompt_version
    elif prompt is not None:
        version = prompt.version
    else:
        raw = response.metadata.get("prompt_version", "")
        if not raw.strip():
            raise SignalLLMAttachmentError(
                "prompt_version required via Prompt, prompt_version arg, or metadata"
            )
        version = raw
    # Label model output explicitly for explainability (avoid "financial advice" substring).
    reasoning = "Model output (informational only): " f"{response.content.strip()}"
    alt = (
        alternative_scenario
        if alternative_scenario is not None
        else "If key levels break, the thesis may invalidate; reassess with fresh data."
    )
    fomo = (
        fomo_fear_note
        if fomo_fear_note is not None
        else "Treat LLM narrative as uncertain context, not a directive to trade."
    )
    return llm_insight_from_parts(
        reasoning=reasoning,
        alternative_scenario=alt,
        fomo_fear_note=fomo,
        provider=response.provider_id,
        model_name=response.model_name,
        prompt_version=version,
    )
