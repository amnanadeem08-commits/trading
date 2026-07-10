"""Integration tests for AI layer runtime."""

from __future__ import annotations

import pytest

from ai import (
    AgentRegistry,
    AILifecycleEventType,
    AILifecycleManager,
    AIOrchestrator,
    InMemoryAIEvaluator,
    Prompt,
    PromptRegistry,
    get_agent_registry,
    reset_agent_registry,
    reset_llm_registry,
    reset_prompt_registry,
)
from config.settings import get_settings, reset_settings
from core import CoreRuntime, reset_core_runtime
from events.event_bus import EventBus
from pipeline import build_pipeline_context
from services import ApplicationContext, build_application_context, reset_application_context
from tests.ai_helpers import SampleAgent, make_agent_metadata


@pytest.fixture(autouse=True)
def _reset_runtime() -> None:
    reset_application_context()
    reset_agent_registry()
    reset_prompt_registry()
    reset_llm_registry()
    reset_core_runtime()
    reset_settings()
    yield
    reset_application_context()
    reset_agent_registry()
    reset_prompt_registry()
    reset_llm_registry()
    reset_core_runtime()
    reset_settings()


@pytest.mark.integration
def test_ai_runtime_full_orchestration_flow() -> None:
    settings = get_settings()
    assert settings.ai.orchestration_enabled is True
    assert settings.ai.lifecycle_enabled is True

    bus = EventBus()
    application = build_application_context()
    updated_app = ApplicationContext(
        settings=application.settings,
        feature_flags=application.feature_flags,
        event_bus=bus,
        metrics=application.metrics,
        health=application.health,
        audit=application.audit,
        version_registry=application.version_registry,
        logger_factory=application.logger_factory,
        configuration_hash=application.configuration_hash,
    )
    context = build_pipeline_context(updated_app)
    core_runtime = CoreRuntime(context=context)
    core_context = core_runtime.build_context(
        operation_type="ai_pipeline",
        dataset_ids=("records",),
    )
    lifecycle = AILifecycleManager(context)

    agents = AgentRegistry()
    prompts = PromptRegistry()
    agents.register(make_agent_metadata())
    agents.register_type(SampleAgent)
    prompts.register(
        Prompt(prompt_id="task-prompt", name="Task", version="1.0.0", content="Execute task"),
    )

    orchestrator = AIOrchestrator(agent_registry=agents, prompt_registry=prompts)
    lifecycle.emit(
        AILifecycleEventType.AGENT_STARTED,
        agent_id="sample-agent",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="starting",
    )
    task = orchestrator.create_task(
        agent_id="sample-agent",
        core_context=core_context,
        prompt_id="task-prompt",
        input_data={"record_id": "1"},
    )
    lifecycle.emit(
        AILifecycleEventType.PROMPT_EXECUTED,
        agent_id="sample-agent",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="prompt executed",
        payload={"prompt_id": "task-prompt"},
    )
    result = orchestrator.execute(task, SampleAgent())
    lifecycle.emit(
        AILifecycleEventType.LLM_REQUEST_COMPLETED,
        agent_id="sample-agent",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="llm done",
    )
    lifecycle.emit(
        AILifecycleEventType.REASONING_COMPLETED,
        agent_id="sample-agent",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="reasoning done",
    )
    lifecycle.emit(
        AILifecycleEventType.AGENT_COMPLETED,
        agent_id="sample-agent",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="completed",
    )

    evaluator = InMemoryAIEvaluator()
    evaluation = evaluator.evaluate(
        agent_id="sample-agent",
        task_id=task.task_id,
        result=result,
    )
    lifecycle.emit(
        AILifecycleEventType.AI_EVALUATION_COMPLETED,
        agent_id="sample-agent",
        correlation_id=core_context.correlation_id,
        trace_id=core_context.trace_id,
        message="evaluation done",
        payload={"evaluation_id": evaluation.evaluation_id},
    )

    assert result.confidence >= 0.9
    assert evaluation.quality_score >= 0.9
    assert bus.persistence.count() >= 6
    assert len(lifecycle.events) >= 6


@pytest.mark.integration
def test_ai_runtime_singleton_registry() -> None:
    registry = get_agent_registry()
    registry.register(make_agent_metadata(agent_id="singleton"))
    assert get_agent_registry().list() == ("singleton",)
