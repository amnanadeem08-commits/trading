"""Domain event type aliases and handler contracts."""

from __future__ import annotations

from collections.abc import Callable

from models.events import (
    AuditRecord,
    DecisionCreatedEvent,
    DomainEvent,
    EventType,
    OutcomeCapturedEvent,
    PredictionCreatedEvent,
    RiskEvaluatedEvent,
    ValidationCompletedEvent,
)

type EventHandler = Callable[[DomainEvent], None]

__all__ = [
    "AuditRecord",
    "DecisionCreatedEvent",
    "DomainEvent",
    "EventHandler",
    "EventType",
    "OutcomeCapturedEvent",
    "PredictionCreatedEvent",
    "RiskEvaluatedEvent",
    "ValidationCompletedEvent",
]
