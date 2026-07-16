"""Paper trading lifecycle events and deterministic audit records (PAPER-005).

This module emits domain events via the shared in-process `EventBus` and writes
append-only audit records via `AuditLogger`.

Idempotency: lifecycle events are keyed by deterministic `event_id` values.
We skip publishing/writing when an audit record for the same `event_id` already
exists (append-only store → safe exactly-once per event_id).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from audit import AuditLogger, AuditReader
from events import EventBus
from events.event_types import EventType
from legacy_config import TIMEFRAME
from models.common import UTCDateTime
from models.events import AuditRecord, DomainEvent
from models.signal import ExplainableSignal
from paper_trading.contracts.ledger import PositionStatus
from paper_trading.contracts.paper_fill import PaperFillResult


def _deterministic_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]
    return f"{prefix}-{digest}"


def _iso(ts: UTCDateTime) -> str:
    # Normalize to stable ISO string representation.
    return ts.isoformat()


def _execution_result_payload(*, event: DomainEvent) -> str:
    # Stored as JSON in `AuditRecord.execution_result`.
    # Includes identifiers and lifecycle context for deterministic export.
    return json.dumps(
        {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "correlation_id": event.correlation_id,
            "occurred_at": event.occurred_at.isoformat(),
            "payload": event.payload,
        },
        sort_keys=True,
        default=str,
    )


@dataclass(frozen=True)
class _LifecycleContext:
    session_id: str
    signal_id: str
    symbol_id: str
    market_id: str
    timeframe: str
    fill_id: str | None


class PaperTradingLifecycleService:
    """Emit paper lifecycle events + deterministic audit records (PAPER-005)."""

    def __init__(
        self,
        *,
        event_bus: EventBus,
        audit_logger: AuditLogger,
    ) -> None:
        self._event_bus = event_bus
        self._audit_logger = audit_logger
        self._audit_reader = AuditReader(audit_logger.store)

    def emit_fill_accepted(
        self,
        *,
        signal: ExplainableSignal,
        result: PaperFillResult,
        reason: str | None = None,
        occurred_at: UTCDateTime | None = None,
    ) -> None:
        """Emit fill accepted + related position/PnL lifecycle outcomes."""
        occurred_at = occurred_at or result.fill.filled_at
        ctx = _LifecycleContext(
            session_id=result.session_id,
            signal_id=result.signal_id,
            symbol_id=result.symbol_id,
            market_id=result.market_id,
            timeframe=TIMEFRAME,
            fill_id=result.fill.fill_id,
        )
        reason = reason or result.message

        self._emit_stage(
            ctx=ctx,
            signal=signal,
            event_stage="fill_accepted",
            lifecycle_status=result.status.value,
            occurred_at=occurred_at,
            reason=reason,
            extra_payload={
                "fill_id": result.fill.fill_id,
                "trade_id": result.fill.trade_id,
                "order_request_id": result.fill.request_id,
                "decision": result.decision.value,
            },
        )

        # Position lifecycle outcomes based on the append-only ledger row we just wrote.
        pos = result.position_entry
        if pos.status == PositionStatus.OPEN:
            self._emit_stage(
                ctx=ctx,
                signal=signal,
                event_stage="position_opened",
                lifecycle_status="position_opened",
                occurred_at=pos.opened_at,
                reason=reason,
                extra_payload={
                    "position_id": pos.position_id,
                    "side": pos.side.value,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "fill_price": pos.fill_price,
                },
            )
            if result.status.value == "partially_filled":
                self._emit_stage(
                    ctx=ctx,
                    signal=signal,
                    event_stage="position_updated",
                    lifecycle_status="position_updated",
                    occurred_at=pos.opened_at,
                    reason=reason,
                    extra_payload={
                        "position_id": pos.position_id,
                        "side": pos.side.value,
                        "quantity": pos.quantity,
                    },
                )
        elif pos.status == PositionStatus.CLOSED:
            self._emit_stage(
                ctx=ctx,
                signal=signal,
                event_stage="position_closed",
                lifecycle_status="position_closed",
                occurred_at=pos.closed_at or occurred_at,
                reason=reason,
                extra_payload={
                    "position_id": pos.position_id,
                    "side": pos.side.value,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "fill_price": pos.fill_price,
                },
            )
            self._emit_stage(
                ctx=ctx,
                signal=signal,
                event_stage="realized_pnl_recorded",
                lifecycle_status="realized_pnl_recorded",
                occurred_at=result.pnl_entry.timestamp,
                reason=reason,
                extra_payload={
                    "position_id": pos.position_id,
                    "trade_id": result.pnl_entry.trade_id,
                    "realized_pnl": result.pnl_entry.realized_pnl,
                    "commission": result.pnl_entry.commission,
                    "slippage": result.pnl_entry.slippage,
                },
            )

    def emit_fill_rejected(
        self,
        *,
        signal: ExplainableSignal,
        session_id: str,
        reason: str,
        risk_reasons: tuple[str, ...] = (),
        occurred_at: UTCDateTime,
    ) -> None:
        """Emit fill rejected outcome (no ledger/portfolio mutation)."""
        ctx = _LifecycleContext(
            session_id=session_id,
            signal_id=signal.signal_id,
            symbol_id=signal.symbol_id,
            market_id=signal.market_id,
            timeframe=TIMEFRAME,
            fill_id=None,
        )
        self._emit_stage(
            ctx=ctx,
            signal=signal,
            event_stage="fill_rejected",
            lifecycle_status="fill_rejected",
            occurred_at=occurred_at,
            reason=reason,
            extra_payload={
                "risk_reasons": list(risk_reasons),
                "decision": signal.decision.value,
            },
        )

        # A rejected fill is a lifecycle failure from the perspective of
        # downstream consumers.
        self._emit_stage(
            ctx=ctx,
            signal=signal,
            event_stage="lifecycle_failure",
            lifecycle_status="lifecycle_failure",
            occurred_at=occurred_at,
            reason=reason,
            extra_payload={
                "failure_kind": "fill_rejected",
                "risk_reasons": list(risk_reasons),
            },
        )

    def emit_cancellation(
        self,
        *,
        signal: ExplainableSignal,
        session_id: str,
        reason: str,
        occurred_at: UTCDateTime,
    ) -> None:
        """Emit cancelled outcome (no ledger/portfolio mutation)."""
        ctx = _LifecycleContext(
            session_id=session_id,
            signal_id=signal.signal_id,
            symbol_id=signal.symbol_id,
            market_id=signal.market_id,
            timeframe=TIMEFRAME,
            fill_id=None,
        )
        self._emit_stage(
            ctx=ctx,
            signal=signal,
            event_stage="cancelled",
            lifecycle_status="cancelled",
            occurred_at=occurred_at,
            reason=reason,
            extra_payload={},
        )

    def _emit_stage(
        self,
        *,
        ctx: _LifecycleContext,
        signal: ExplainableSignal,
        event_stage: str,
        lifecycle_status: str,
        occurred_at: UTCDateTime,
        reason: str,
        extra_payload: dict[str, object] | None = None,
    ) -> None:
        extra_payload = extra_payload or {}
        event_id = _deterministic_id(
            "paper-event",
            event_stage,
            ctx.session_id,
            ctx.signal_id,
            ctx.symbol_id,
            ctx.timeframe,
            ctx.fill_id or "",
            _iso(occurred_at),
        )
        correlation_id = _deterministic_id(
            "paper-corr",
            ctx.session_id,
            ctx.signal_id,
            ctx.symbol_id,
        )

        event = DomainEvent(
            event_id=event_id,
            event_type=EventType.TRADE_EXECUTED,
            correlation_id=correlation_id,
            market_id=ctx.market_id,
            symbol_id=ctx.symbol_id,
            occurred_at=occurred_at,
            payload={
                "timeframe": ctx.timeframe,
                "session_id": ctx.session_id,
                "signal_id": ctx.signal_id,
                "fill_id": ctx.fill_id,
                "lifecycle_status": lifecycle_status,
                "reason": reason,
                **extra_payload,
            },
        )

        if self._audit_exists(event.event_id):
            return

        # Publish the domain event (append-only persistence + in-process subscribers).
        self._event_bus.publish(event)

        # Deterministic, append-only audit record.
        audit = self._audit_from_event(
            event=event,
            signal=signal,
            timestamp=occurred_at,
            execution_result=_execution_result_payload(event=event),
        )
        self._audit_logger.write(audit)

    def _audit_exists(self, event_id: str) -> bool:
        audits = self._audit_reader.read(event_id=event_id)
        return len(audits) > 0

    def _audit_from_event(
        self,
        *,
        event: DomainEvent,
        signal: ExplainableSignal,
        timestamp: UTCDateTime,
        execution_result: str,
    ) -> AuditRecord:
        # Note: `AuditRecord` doesn't have dedicated lifecycle fields.
        # We encode lifecycle context inside `execution_result` for deterministic export.
        return AuditRecord(
            audit_id=_deterministic_id("paper-audit", event.event_id),
            event_id=event.event_id,
            timestamp=timestamp,
            user_id="paper-lifecycle",
            market_id=event.market_id,
            symbol_id=event.symbol_id,
            connector_version=signal.provenance.connector_version,
            broker_version=None,
            strategy_version=signal.provenance.strategy_version,
            model_version=signal.reproducibility.model_version,
            prompt_version=signal.provenance.prompt_version,
            feature_snapshot_version=signal.provenance.feature_snapshot_version,
            confidence=signal.confidence,
            decision=signal.decision,
            risk_verdict=None,
            execution_result=execution_result,
            validation_outcome=None,
            reproducibility=signal.reproducibility,
            feature_flags_active={"PAPER_TRADING_ONLY": True},
        )


_default_service: PaperTradingLifecycleService | None = None


def get_default_paper_lifecycle_service() -> PaperTradingLifecycleService:
    global _default_service
    if _default_service is None:
        from events.event_bus import get_event_bus

        _default_service = PaperTradingLifecycleService(
            event_bus=get_event_bus(),
            audit_logger=AuditLogger(),
        )
    return _default_service


def set_default_paper_lifecycle_service(
    service: PaperTradingLifecycleService | None,
) -> None:
    """Override the default lifecycle service (used by tests)."""
    global _default_service
    _default_service = service
