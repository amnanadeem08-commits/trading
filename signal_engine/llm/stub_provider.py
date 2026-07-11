"""Stub LLM insight provider for tests and local wiring."""

from __future__ import annotations

from models.common import VersionInfo
from models.prediction import LLMInsight, MLPrediction
from signal_engine.contracts.assembly_request import SignalAssemblyRequest
from signal_engine.exceptions import SignalLLMAttachmentError
from signal_engine.llm.insight_mapper import llm_insight_from_parts


class StubLLMInsightProvider:
    """Deterministic safe insight provider (no live LLM calls)."""

    def __init__(
        self,
        *,
        prompt_version: str = "prompt-stub-1",
        provider: str = "stub-llm",
        model_name: str = "stub-reasoner",
        fail: bool = False,
        unsafe: bool = False,
    ) -> None:
        self._prompt_version = prompt_version
        self._provider = provider
        self._model_name = model_name
        self._fail = fail
        self._unsafe = unsafe

    def get_insight(
        self,
        *,
        request: SignalAssemblyRequest,
        prediction: MLPrediction,
    ) -> LLMInsight:
        if self._fail:
            raise SignalLLMAttachmentError(
                f"stub LLM provider forced failure for {request.symbol_id}"
            )
        reasoning = (
            "Model output (informational only): "
            f"ML leans {prediction.direction.value} with confidence "
            f"{prediction.ml_confidence:.2f} on {request.symbol_id}."
        )
        if self._unsafe:
            reasoning = "This is guaranteed profit financial advice."
        return llm_insight_from_parts(
            reasoning=reasoning,
            alternative_scenario=(
                "If invalidation triggers, stand aside and reassess; no obligatory action."
            ),
            fomo_fear_note=(
                "Ignore urgency narratives; this text is uncertain model commentary only."
            ),
            provider=self._provider,
            model_name=self._model_name,
            prompt_version=VersionInfo(version_id=self._prompt_version),
        )
