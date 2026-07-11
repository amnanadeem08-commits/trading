"""Attach LLMInsight onto SignalAssemblyRequest."""

from __future__ import annotations

from models.decision import DecisionSource
from models.prediction import LLMInsight, MLPrediction
from signal_engine.contracts.assembly_request import SignalAssemblyRequest
from signal_engine.exceptions import SignalLLMAttachmentError
from signal_engine.llm.insight_port import LLMInsightProvider
from signal_engine.llm.safety import assert_safe_insight_text


def attach_llm_insight(
    request: SignalAssemblyRequest,
    insight: LLMInsight,
    *,
    require_ml_prediction: bool = True,
) -> SignalAssemblyRequest:
    """Attach insight for AI-enhanced signals and sync provenance.prompt_version."""
    assert_safe_insight_text(
        insight.reasoning,
        insight.alternative_scenario,
        insight.fomo_fear_note,
    )
    if require_ml_prediction and request.ml_prediction is None:
        raise SignalLLMAttachmentError(
            "ml_prediction is required before attaching llm_insight for AI-enhanced path"
        )
    provenance = request.provenance.model_copy(
        update={"prompt_version": insight.prompt_version.version_id}
    )
    attached = request.model_copy(
        update={
            "llm_insight": insight,
            "decision_source": DecisionSource.AI_ENHANCED_ML,
            "alternative_scenario": insight.alternative_scenario,
            "provenance": provenance,
        }
    )
    ensure_llm_insight_present(attached)
    return attached


def attach_llm_insight_from_provider(
    request: SignalAssemblyRequest,
    provider: LLMInsightProvider,
    *,
    prediction: MLPrediction | None = None,
) -> SignalAssemblyRequest:
    """Resolve insight from a provider port and attach it."""
    ml_prediction = prediction if prediction is not None else request.ml_prediction
    if ml_prediction is None:
        raise SignalLLMAttachmentError("ML prediction required to generate AI-enhanced LLM insight")
    try:
        insight = provider.get_insight(request=request, prediction=ml_prediction)
    except SignalLLMAttachmentError:
        raise
    except Exception as error:
        msg = f"LLM insight provider failed: {error}"
        raise SignalLLMAttachmentError(msg) from error
    return attach_llm_insight(request, insight, require_ml_prediction=True)


def ensure_llm_insight_present(request: SignalAssemblyRequest) -> None:
    """Fail explicitly when AI-enhanced source lacks llm_insight."""
    if request.decision_source == DecisionSource.AI_ENHANCED_ML and request.llm_insight is None:
        raise SignalLLMAttachmentError(
            "llm_insight is required when decision_source is ai_enhanced_ml"
        )
    if request.llm_insight is not None:
        assert_safe_insight_text(
            request.llm_insight.reasoning,
            request.llm_insight.alternative_scenario,
            request.llm_insight.fomo_fear_note,
        )
