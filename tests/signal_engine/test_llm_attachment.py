"""Unit tests for LLM insight attachment."""

from __future__ import annotations

import pytest

from ai.llm.llm_response import LLMResponse
from ai.prompts.prompt import Prompt
from models.common import VersionInfo
from models.decision import DecisionSource
from signal_engine import (
    SignalAssembler,
    SignalLLMAttachmentError,
    StubLLMInsightProvider,
    assert_safe_insight_text,
    attach_llm_insight,
    attach_llm_insight_from_provider,
    attach_ml_prediction,
    ensure_llm_insight_present,
    llm_insight_from_llm_response,
    llm_insight_from_parts,
)
from tests.signal_helpers import (
    make_assembly_request,
    make_llm_insight,
    make_ml_prediction,
)


def _with_ml():
    return attach_ml_prediction(
        make_assembly_request(),
        make_ml_prediction(),
        decision_source=DecisionSource.ML_ONLY,
    )


@pytest.mark.unit
def test_llm_insight_from_parts_and_safety() -> None:
    insight = llm_insight_from_parts(
        reasoning="Model output (informational only): momentum is mixed.",
        alternative_scenario="Break of support would weaken the thesis.",
        fomo_fear_note="Do not treat narrative urgency as a directive.",
        provider="stub-llm",
        model_name="stub-reasoner",
        prompt_version="prompt-v1",
    )
    assert insight.prompt_version.version_id == "prompt-v1"
    with pytest.raises(SignalLLMAttachmentError, match="forbidden framing"):
        assert_safe_insight_text("This offers guaranteed profit tomorrow.")
    with pytest.raises(SignalLLMAttachmentError, match="forbidden framing"):
        llm_insight_from_parts(
            reasoning="Buy now — this is financial advice.",
            alternative_scenario="n/a",
            fomo_fear_note="n/a",
            provider="x",
            model_name="y",
            prompt_version="p1",
        )


@pytest.mark.unit
def test_llm_insight_from_llm_response_paths() -> None:
    response = LLMResponse(
        request_id="r1",
        provider_id="anthropic",
        content="Trend context is constructive but uncertain.",
        model_name="claude-test",
        metadata={"prompt_version": "meta-prompt-1"},
    )
    from_meta = llm_insight_from_llm_response(response)
    assert from_meta.prompt_version.version_id == "meta-prompt-1"
    assert from_meta.reasoning.startswith("Model output (informational only):")

    prompt = Prompt(
        prompt_id="p1",
        name="signal-insight",
        version="prompt-from-registry",
        content="Explain the ML lean without directives.",
    )
    from_prompt = llm_insight_from_llm_response(
        response.model_copy(update={"metadata": {}}),
        prompt=prompt,
    )
    assert from_prompt.prompt_version.version_id == "prompt-from-registry"

    with pytest.raises(SignalLLMAttachmentError, match="empty"):
        llm_insight_from_llm_response(
            response.model_copy(update={"content": "  ", "metadata": {"prompt_version": "p"}})
        )
    with pytest.raises(SignalLLMAttachmentError, match="prompt_version"):
        llm_insight_from_llm_response(response.model_copy(update={"metadata": {}}))


@pytest.mark.unit
def test_attach_llm_insight_wires_assembler_and_prompt_version() -> None:
    insight = make_llm_insight()
    request = attach_llm_insight(_with_ml(), insight)
    assert request.decision_source == DecisionSource.AI_ENHANCED_ML
    assert request.llm_insight is not None
    assert request.provenance.prompt_version == insight.prompt_version.version_id
    signal = SignalAssembler().assemble(request)
    assert signal.llm_insight is not None
    assert signal.decision_source == DecisionSource.AI_ENHANCED_ML
    assert signal.provenance.prompt_version == "prompt-1"


@pytest.mark.unit
def test_attach_from_provider_and_failure_modes() -> None:
    provider = StubLLMInsightProvider(prompt_version="prompt-stub-9")
    request = attach_llm_insight_from_provider(_with_ml(), provider)
    assert request.llm_insight is not None
    assert request.provenance.prompt_version == "prompt-stub-9"
    assert request.decision_source == DecisionSource.AI_ENHANCED_ML

    with pytest.raises(SignalLLMAttachmentError, match="forced failure"):
        attach_llm_insight_from_provider(
            _with_ml(),
            StubLLMInsightProvider(fail=True),
        )

    with pytest.raises(SignalLLMAttachmentError, match="forbidden framing"):
        attach_llm_insight_from_provider(
            _with_ml(),
            StubLLMInsightProvider(unsafe=True),
        )

    bare = make_assembly_request()
    with pytest.raises(SignalLLMAttachmentError, match="ml_prediction is required"):
        attach_llm_insight(bare, make_llm_insight())

    with pytest.raises(SignalLLMAttachmentError, match="ML prediction required"):
        attach_llm_insight_from_provider(bare, provider)

    missing = make_assembly_request(
        decision_source=DecisionSource.AI_ENHANCED_ML,
        ml_prediction=make_ml_prediction(),
        llm_insight=None,
    )
    with pytest.raises(SignalLLMAttachmentError, match="llm_insight is required"):
        ensure_llm_insight_present(missing)


@pytest.mark.unit
def test_provider_unexpected_exception_is_wrapped() -> None:
    class BrokenProvider:
        def get_insight(self, *, request: object, prediction: object) -> object:
            raise RuntimeError("boom")

    with pytest.raises(SignalLLMAttachmentError, match="provider failed"):
        attach_llm_insight_from_provider(_with_ml(), BrokenProvider())  # type: ignore[arg-type]


@pytest.mark.unit
def test_mapper_rejects_empty_provider_fields() -> None:
    with pytest.raises(SignalLLMAttachmentError, match="provider and model_name"):
        llm_insight_from_parts(
            reasoning="ok",
            alternative_scenario="ok",
            fomo_fear_note="ok",
            provider="  ",
            model_name="m",
            prompt_version=VersionInfo(version_id="p"),
        )
    with pytest.raises(SignalLLMAttachmentError, match="prompt_version"):
        llm_insight_from_parts(
            reasoning="ok",
            alternative_scenario="ok",
            fomo_fear_note="ok",
            provider="p",
            model_name="m",
            prompt_version="  ",
        )
