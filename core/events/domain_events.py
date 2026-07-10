"""Generic core domain event contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class CoreDomainEventType(StrEnum):
    """Registered core domain event identifiers."""

    DATASET_LOADED = "dataset_loaded"
    RESOURCE_CREATED = "resource_created"
    EVALUATION_COMPLETED = "evaluation_completed"
    DECISION_GENERATED = "decision_generated"


class CoreDomainEvent(PlatformModel):
    """Base contract for core domain events."""

    event_id: str = Field(min_length=1)
    event_type: CoreDomainEventType
    correlation_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    occurred_at: UTCDateTime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)


class DatasetLoadedEvent(CoreDomainEvent):
    """Emitted when a dataset is loaded into runtime context."""

    event_type: CoreDomainEventType = CoreDomainEventType.DATASET_LOADED
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    record_count: int = Field(ge=0, default=0)


class ResourceCreatedEvent(CoreDomainEvent):
    """Emitted when a platform resource is created."""

    event_type: CoreDomainEventType = CoreDomainEventType.RESOURCE_CREATED
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    resource_version: str = Field(min_length=1)


class EvaluationCompletedEvent(CoreDomainEvent):
    """Emitted when an evaluation operation completes."""

    event_type: CoreDomainEventType = CoreDomainEventType.EVALUATION_COMPLETED
    evaluation_id: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    score: float | None = Field(default=None, ge=0.0, le=1.0)


class DecisionGeneratedEvent(CoreDomainEvent):
    """Emitted when a decision artifact is generated."""

    event_type: CoreDomainEventType = CoreDomainEventType.DECISION_GENERATED
    decision_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    outcome_type: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
