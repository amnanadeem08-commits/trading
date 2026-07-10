"""Domain event contracts. Typed, versioned, traceable."""

from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import Field, field_validator

from models.common import PlatformModel, ReproducibilityKey, UTCDateTime, utc_now
from models.decision import DecisionSource, DecisionState, TradingDecision
from models.risk import RiskVerdictStatus
from models.validation import ValidationOutcomeStatus


class EventType(StrEnum):
    """Registered domain event types."""

    PREDICTION_CREATED = "prediction_created"
    DECISION_CREATED = "decision_created"
    RISK_EVALUATED = "risk_evaluated"
    TRADE_EXECUTED = "trade_executed"
    OUTCOME_CAPTURED = "outcome_captured"
    VALIDATION_COMPLETED = "validation_completed"


class DomainEvent(PlatformModel):
    """Base domain event. All events are versioned and traceable."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: EventType
    event_version: str = Field(default="1.0.0", min_length=1)
    correlation_id: str = Field(default_factory=lambda: str(uuid4()))
    causation_id: str | None = None
    market_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    occurred_at: UTCDateTime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_version")
    @classmethod
    def validate_semver_like(cls, value: str) -> str:
        parts = value.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            msg = "event_version must follow MAJOR.MINOR.PATCH format"
            raise ValueError(msg)
        return value


class PredictionCreatedEvent(DomainEvent):
    """Emitted when a prediction/explainable signal is created."""

    event_type: EventType = EventType.PREDICTION_CREATED
    signal_id: str = Field(min_length=1)
    decision: DecisionState
    decision_source: DecisionSource
    confidence: float = Field(ge=0.0, le=1.0)
    reproducibility: ReproducibilityKey


class DecisionCreatedEvent(DomainEvent):
    """Emitted when Decision Engine produces a TradingDecision."""

    event_type: EventType = EventType.DECISION_CREATED
    decision: TradingDecision


class RiskEvaluatedEvent(DomainEvent):
    """Emitted when Risk Engine evaluates a decision."""

    event_type: EventType = EventType.RISK_EVALUATED
    verdict_id: str = Field(min_length=1)
    decision_id: str = Field(min_length=1)
    status: RiskVerdictStatus
    rejection_reason: str | None = None


class OutcomeCapturedEvent(DomainEvent):
    """Emitted when actual market outcome is recorded."""

    event_type: EventType = EventType.OUTCOME_CAPTURED
    prediction_id: str = Field(min_length=1)
    actual_outcome: str = Field(min_length=1)


class ValidationCompletedEvent(DomainEvent):
    """Emitted when validation loop completes for a prediction."""

    event_type: EventType = EventType.VALIDATION_COMPLETED
    validation_id: str = Field(min_length=1)
    prediction_id: str = Field(min_length=1)
    status: ValidationOutcomeStatus
    accuracy_score: float | None = Field(default=None, ge=0.0, le=1.0)


class AuditRecord(PlatformModel):
    """Permanent audit record per Rule R15."""

    audit_id: str = Field(default_factory=lambda: str(uuid4()))
    event_id: str = Field(min_length=1)
    timestamp: UTCDateTime = Field(default_factory=utc_now)
    user_id: str = Field(default="system", min_length=1)
    market_id: str = Field(min_length=1)
    symbol_id: str = Field(min_length=1)
    connector_version: str = Field(min_length=1)
    broker_version: str | None = None
    strategy_version: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    feature_snapshot_version: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    decision: DecisionState
    risk_verdict: RiskVerdictStatus | None = None
    execution_result: str | None = None
    validation_outcome: ValidationOutcomeStatus | None = None
    reproducibility: ReproducibilityKey
    feature_flags_active: dict[str, bool] = Field(default_factory=dict)
