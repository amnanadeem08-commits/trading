"""AI orchestrator."""

from __future__ import annotations

from uuid import uuid4

from ai.agents.agent import Agent
from ai.agents.agent_context import AgentContext
from ai.agents.agent_lifecycle import AgentState
from ai.agents.agent_registry import AgentRegistry
from ai.exceptions import AgentNotFoundError, OrchestrationError
from ai.llm.llm_registry import LLMRegistry
from ai.llm.llm_request import LLMRequest
from ai.llm.llm_response import LLMResponse
from ai.orchestration.ai_task import AITask
from ai.prompts.prompt_registry import PromptRegistry
from ai.reasoning.reasoning_context import ReasoningContext
from ai.reasoning.reasoning_engine import ReasoningEngine
from ai.reasoning.reasoning_result import ReasoningResult
from core.context.core_context import CoreContext


class AIOrchestrator:
    """Coordinates AI task execution across agents, prompts, LLM, and reasoning."""

    def __init__(
        self,
        *,
        agent_registry: AgentRegistry | None = None,
        prompt_registry: PromptRegistry | None = None,
        llm_registry: LLMRegistry | None = None,
        reasoning_engine: ReasoningEngine | None = None,
    ) -> None:
        from ai.llm.llm_provider import StubLLMProvider
        from ai.reasoning.reasoning_engine import PassthroughReasoningEngine

        self._agents = agent_registry or AgentRegistry()
        self._prompts = prompt_registry or PromptRegistry()
        self._llm = llm_registry or LLMRegistry()
        self._reasoning = reasoning_engine or PassthroughReasoningEngine()
        if not self._llm.exists("stub"):
            self._llm.register(StubLLMProvider())

    def create_task(
        self,
        *,
        agent_id: str,
        core_context: CoreContext | None = None,
        prompt_id: str | None = None,
        provider_id: str | None = None,
        model_id: str | None = None,
        input_data: dict[str, object] | None = None,
    ) -> AITask:
        if not self._agents.exists(agent_id):
            raise AgentNotFoundError(agent_id)
        task_id = str(uuid4())
        agent_context = AgentContext(
            agent_id=agent_id,
            task_id=task_id,
            core_context=core_context,
            model_id=model_id,
            prompt_id=prompt_id,
            provider_id=provider_id or "stub",
        )
        return AITask(
            task_id=task_id,
            agent_id=agent_id,
            prompt_id=prompt_id,
            provider_id=provider_id or "stub",
            model_id=model_id,
            agent_context=agent_context,
            input_data=input_data or {},
        )

    def execute(self, task: AITask, agent: Agent) -> ReasoningResult:
        """Execute an AI task through the orchestration pipeline."""
        self._agents.set_state(task.agent_id, AgentState.RUNNING)
        context = agent.initialize(
            task.agent_context
            or AgentContext(
                agent_id=task.agent_id,
                task_id=task.task_id,
            )
        )
        try:
            prompt_content = self._resolve_prompt(task)
            llm_response = self._invoke_llm(task, prompt_content)
            reasoning_context = ReasoningContext(
                reasoning_id=str(uuid4()),
                agent_context=context,
                input_data={
                    "task_input": task.input_data,
                    "llm_content": llm_response.content,
                },
            )
            result = self._reasoning.reason(reasoning_context)
            agent_result = agent.execute(context)
            merged = result.model_copy(
                update={
                    "output": {**result.output, **agent_result.output},
                    "metadata": {**result.metadata, **agent_result.metadata},
                    "confidence": max(result.confidence, agent_result.confidence),
                },
            )
            self._agents.set_state(task.agent_id, AgentState.COMPLETED)
            return merged
        except Exception as error:
            self._agents.set_state(task.agent_id, AgentState.FAILED)
            msg = f"AI task execution failed: {error}"
            raise OrchestrationError(msg) from error

    def _resolve_prompt(self, task: AITask) -> str:
        if task.prompt_id is None:
            return ""
        prompt = self._prompts.resolve(task.prompt_id)
        return prompt.content

    def _invoke_llm(self, task: AITask, prompt_content: str) -> LLMResponse:
        provider_id = task.provider_id or "stub"
        provider = self._llm.resolve(provider_id)
        request = LLMRequest(
            request_id=str(uuid4()),
            provider_id=provider_id,
            prompt=prompt_content or f"task:{task.task_id}",
        )
        return provider.complete(request)
