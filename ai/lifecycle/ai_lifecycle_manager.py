"""AI lifecycle events and manager."""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from threading import RLock
from typing import Any
from uuid import uuid4

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from models.events import DomainEvent, EventType
from pipeline.context import PipelineContext

type LifecycleHandler = Callable[["AILifecycleEvent"], None]

INFRASTRUCTURE_SCOPE_ID = "platform"
INFRASTRUCTURE_ENTITY_ID = "ai"


class AILifecycleEventType(StrEnum):
    """AI lifecycle event identifiers."""

    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    PROMPT_EXECUTED = "prompt_executed"
    LLM_REQUEST_COMPLETED = "llm_request_completed"
    REASONING_COMPLETED = "reasoning_completed"
    AI_EVALUATION_COMPLETED = "ai_evaluation_completed"


class AILifecycleEvent(PlatformModel):
    """Lifecycle event emitted by the AI layer."""

    event_id: str
    event_type: AILifecycleEventType
    agent_id: str
    correlation_id: str
    trace_id: str
    message: str
    occurred_at: UTCDateTime
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentStartedEvent(AILifecycleEvent):
    """Emitted when an agent execution starts."""

    event_type: AILifecycleEventType = AILifecycleEventType.AGENT_STARTED


class AgentCompletedEvent(AILifecycleEvent):
    """Emitted when an agent execution completes."""

    event_type: AILifecycleEventType = AILifecycleEventType.AGENT_COMPLETED


class PromptExecutedEvent(AILifecycleEvent):
    """Emitted when a prompt is executed."""

    event_type: AILifecycleEventType = AILifecycleEventType.PROMPT_EXECUTED
    prompt_id: str = Field(min_length=1)


class LLMRequestCompletedEvent(AILifecycleEvent):
    """Emitted when an LLM request completes."""

    event_type: AILifecycleEventType = AILifecycleEventType.LLM_REQUEST_COMPLETED
    provider_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1)


class ReasoningCompletedEvent(AILifecycleEvent):
    """Emitted when reasoning completes."""

    event_type: AILifecycleEventType = AILifecycleEventType.REASONING_COMPLETED
    reasoning_id: str = Field(min_length=1)


class AIEvaluationCompletedEvent(AILifecycleEvent):
    """Emitted when AI evaluation completes."""

    event_type: AILifecycleEventType = AILifecycleEventType.AI_EVALUATION_COMPLETED
    evaluation_id: str = Field(min_length=1)


class AILifecycleManager:
    """Manages AI lifecycle events and EventBus publication."""

    def __init__(self, context: PipelineContext) -> None:
        self._context = context
        self._lock = RLock()
        self._handlers: dict[str, LifecycleHandler] = {}
        self._events: list[AILifecycleEvent] = []

    @property
    def events(self) -> tuple[AILifecycleEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def on_event(self, handler: LifecycleHandler) -> str:
        subscription_id = str(uuid4())
        with self._lock:
            self._handlers[subscription_id] = handler
        return subscription_id

    def off_event(self, subscription_id: str) -> None:
        with self._lock:
            self._handlers.pop(subscription_id, None)

    def emit(
        self,
        event_type: AILifecycleEventType,
        *,
        agent_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> AILifecycleEvent:
        event = AILifecycleEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            agent_id=agent_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
            occurred_at=utc_now(),
            payload=payload or {},
        )
        with self._lock:
            self._events.append(event)
            handlers = tuple(self._handlers.values())
        for handler in handlers:
            handler(event)
        self._publish_to_event_bus(event)
        self._record_metrics(event)
        return event

    def _publish_to_event_bus(self, event: AILifecycleEvent) -> None:
        event_type_map = {
            AILifecycleEventType.AGENT_STARTED: EventType.PREDICTION_CREATED,
            AILifecycleEventType.AGENT_COMPLETED: EventType.PREDICTION_CREATED,
            AILifecycleEventType.PROMPT_EXECUTED: EventType.VALIDATION_COMPLETED,
            AILifecycleEventType.LLM_REQUEST_COMPLETED: EventType.VALIDATION_COMPLETED,
            AILifecycleEventType.REASONING_COMPLETED: EventType.VALIDATION_COMPLETED,
            AILifecycleEventType.AI_EVALUATION_COMPLETED: EventType.VALIDATION_COMPLETED,
        }
        domain_event = DomainEvent(
            event_id=event.event_id,
            event_type=event_type_map[event.event_type],
            correlation_id=event.correlation_id,
            market_id=INFRASTRUCTURE_SCOPE_ID,
            symbol_id=event.agent_id,
            payload={
                "source": "ai",
                "lifecycle_event": event.event_type.value,
                "agent_id": event.agent_id,
                "trace_id": event.trace_id,
                "message": event.message,
                **event.payload,
            },
        )
        self._context.event_bus.publish(domain_event)

    def _record_metrics(self, event: AILifecycleEvent) -> None:
        self._context.metrics.counter("ai.lifecycle.events").inc(1)
        self._context.metrics.counter(f"ai.lifecycle.{event.event_type.value}").inc(1)
