"""Signal lifecycle: validate → register → emit PredictionCreatedEvent + audit."""

from __future__ import annotations

from audit.audit_logger import AuditLogger
from events.event_bus import EventBus, get_event_bus
from models.events import AuditRecord, DomainEvent, EventType, PredictionCreatedEvent
from models.signal import ExplainableSignal
from signal_engine.assembly.assembler import SignalAssembler
from signal_engine.contracts.assembly_request import SignalAssemblyRequest
from signal_engine.exceptions import SignalValidationError
from signal_engine.registry.signal_record import SignalRecord
from signal_engine.registry.signal_registry import SignalRegistry, get_signal_registry
from signal_engine.validation.validation_result import SignalValidationResult
from signal_engine.validation.validator import SignalValidator


class SignalLifecycleService:
    """Orchestrates validation, registry acceptance, and lifecycle events."""

    def __init__(
        self,
        *,
        registry: SignalRegistry | None = None,
        validator: SignalValidator | None = None,
        assembler: SignalAssembler | None = None,
        event_bus: EventBus | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._registry = registry if registry is not None else get_signal_registry()
        self._validator = validator if validator is not None else SignalValidator()
        self._assembler = assembler if assembler is not None else SignalAssembler()
        self._event_bus = event_bus if event_bus is not None else get_event_bus()
        self._audit_logger = audit_logger if audit_logger is not None else AuditLogger()

    @property
    def registry(self) -> SignalRegistry:
        return self._registry

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def audit_logger(self) -> AuditLogger:
        return self._audit_logger

    def validate(self, signal: ExplainableSignal) -> SignalValidationResult:
        """Run structural validation and return accept/reject result."""
        return self._validator.validate(signal)

    def register_signal(self, signal: ExplainableSignal) -> SignalRecord:
        """Validate, register, emit PredictionCreatedEvent, and write audit."""
        result = self._validator.validate(signal)
        if not result.passed:
            self._emit_rejection(signal, result)
            raise SignalValidationError(
                "Signal rejected by validation",
                reasons=result.reasons,
            )
        record = self._registry.register(signal)
        created = PredictionCreatedEvent(
            market_id=signal.market_id,
            symbol_id=signal.symbol_id,
            signal_id=signal.signal_id,
            decision=signal.decision,
            decision_source=signal.decision_source,
            confidence=signal.confidence,
            reproducibility=signal.reproducibility,
            payload={
                "lifecycle_state": "accepted",
                "validated": True,
            },
        )
        self._event_bus.publish(created)
        self._audit_logger.write(_audit_from_signal(signal, event_id=created.event_id))
        return record

    def assemble_and_register(self, request: SignalAssemblyRequest) -> SignalRecord:
        """Assemble from request, then validate/register/emit."""
        signal = self._assembler.assemble(request)
        return self.register_signal(signal)

    def _emit_rejection(
        self,
        signal: ExplainableSignal,
        result: SignalValidationResult,
    ) -> None:
        """Emit explicit rejection event (no registry write)."""
        event = DomainEvent(
            event_type=EventType.VALIDATION_COMPLETED,
            market_id=signal.market_id or "unknown",
            symbol_id=signal.symbol_id or "unknown",
            payload={
                "lifecycle_state": "rejected",
                "signal_id": signal.signal_id,
                "passed": False,
                "reasons": list(result.reasons),
            },
        )
        self._event_bus.publish(event)


def _audit_from_signal(signal: ExplainableSignal, *, event_id: str) -> AuditRecord:
    return AuditRecord(
        event_id=event_id,
        market_id=signal.market_id,
        symbol_id=signal.symbol_id,
        connector_version=signal.provenance.connector_version,
        strategy_version=signal.provenance.strategy_version,
        model_version=signal.reproducibility.model_version,
        prompt_version=signal.provenance.prompt_version,
        feature_snapshot_version=signal.provenance.feature_snapshot_version,
        confidence=signal.confidence,
        decision=signal.decision,
        reproducibility=signal.reproducibility,
    )
