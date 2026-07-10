"""Paper execution adapter implementation."""

from __future__ import annotations

from threading import RLock
from typing import Any

from connectors.adapters.adapter_context import AdapterContext
from connectors.adapters.adapter_metadata import (
    AdapterHealthResult,
    AdapterHealthStatus,
    AdapterMetadata,
)
from connectors.adapters.execution_adapter import ExecutionAdapter
from connectors.adapters.paper.paper_execution_record import PaperExecutionRecord
from connectors.adapters.paper.paper_order_state import PaperState
from connectors.adapters.paper.paper_settings import PaperSettings
from connectors.simulation.simulation_engine import SimulationEngine
from connectors.validation.paper_validator import PaperValidator
from historical.replay.replay_engine import ReplayEngine
from market_data.models.market_record import MarketRecord
from market_data.stream.stream_buffer import StreamBuffer
from models.common import utc_now


def _payload_from_market_record(record: MarketRecord) -> dict[str, object]:
    payload: dict[str, object] = dict(record.attributes)
    payload["timestamp"] = record.timestamp.isoformat()
    payload["record_id"] = record.record_id
    payload["dataset_id"] = record.dataset_id
    payload["symbol_id"] = record.symbol_id
    payload["record_type"] = record.record_type.value
    return payload


PAPER_ADAPTER_ID = "paper-adapter"


class PaperExecutionAdapter(ExecutionAdapter):
    """Offline paper execution adapter with deterministic simulation."""

    def __init__(
        self,
        settings: PaperSettings | None = None,
        *,
        engine: SimulationEngine | None = None,
        validator: PaperValidator | None = None,
        replay_engine: ReplayEngine | None = None,
        stream_buffer: StreamBuffer | None = None,
    ) -> None:
        self._settings = settings or PaperSettings()
        self._engine = engine or SimulationEngine(self._settings)
        self._validator = validator or PaperValidator(self._settings)
        self._replay_engine = replay_engine
        self._stream_buffer = stream_buffer
        self._lock = RLock()
        self._state = PaperState.NEW
        self._records: dict[str, PaperExecutionRecord] = {}

    @property
    def settings(self) -> PaperSettings:
        return self._settings

    @property
    def state(self) -> PaperState:
        with self._lock:
            return self._state

    def adapter_id(self) -> str:
        return PAPER_ADAPTER_ID

    def name(self) -> str:
        return "Paper Execution Adapter"

    def version(self) -> str:
        return "1.0.0"

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_id=self.adapter_id(),
            name=self.name(),
            version=self.version(),
            capabilities=("dispatch", "simulate"),
            tags=("paper", "simulation"),
            attributes={"mode": "offline"},
        )

    def initialize(self, context: AdapterContext) -> None:
        with self._lock:
            self._state = PaperState.ACCEPTED
            record = PaperExecutionRecord(
                record_id=f"record-{context.request_id}",
                execution_id=context.execution_id,
                request_id=context.request_id,
                adapter_id=self.adapter_id(),
                state=PaperState.ACCEPTED,
            )
            self._records[context.request_id] = record

    def validate(self, context: AdapterContext) -> bool:
        result = self._validator.validate_dispatch(context, state=self.state)
        return result.valid

    def dispatch(self, context: AdapterContext) -> dict[str, Any]:
        with self._lock:
            self._state = PaperState.QUEUED
            record = self._records.get(context.request_id)
            if record is not None:
                self._records[context.request_id] = record.model_copy(
                    update={"state": PaperState.QUEUED, "updated_at": utc_now()}
                )

        historical_record: dict[str, object] | None = None
        market_data_stream = False
        if self._stream_buffer is not None:
            stream_step = self._stream_buffer.next()
            if stream_step is not None and stream_step.record is not None:
                historical_record = _payload_from_market_record(stream_step.record)
                market_data_stream = True
        elif self._replay_engine is not None:
            replay_step = self._replay_engine.next()
            if replay_step is not None and replay_step.record is not None:
                historical_record = dict(replay_step.record.payload)

        result = self._engine.simulate(
            request_id=context.request_id,
            execution_id=context.execution_id,
            historical_record=historical_record,
        )

        with self._lock:
            self._state = PaperState.SIMULATED
            record = self._records.get(context.request_id)
            if record is not None:
                self._records[context.request_id] = record.model_copy(
                    update={"state": PaperState.SIMULATED, "updated_at": utc_now()}
                )

        final_state = (
            PaperState.COMPLETED if result.status == PaperState.COMPLETED else PaperState.FAILED
        )
        with self._lock:
            self._state = final_state
            record = self._records.get(context.request_id)
            if record is not None:
                self._records[context.request_id] = record.model_copy(
                    update={"state": final_state, "updated_at": utc_now()}
                )

        output_metadata = dict(result.metadata)
        if market_data_stream:
            output_metadata["market_data_stream"] = "true"

        return {
            "simulated": True,
            "execution_id": result.execution_id,
            "request_id": result.request_id,
            "status": result.status.value,
            "latency_ms": result.latency_ms,
            "duration_ms": result.duration_ms,
            "validation_passed": result.validation_passed,
            "synthetic_fill": dict(result.synthetic_fill),
            "metadata": output_metadata,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat(),
        }

    def shutdown(self, context: AdapterContext) -> None:
        with self._lock:
            self._state = PaperState.CANCELLED
            record = self._records.get(context.request_id)
            if record is not None:
                updated = record.model_copy(
                    update={"state": PaperState.CANCELLED, "updated_at": utc_now()}
                )
                self._records[context.request_id] = updated

    def health(self) -> AdapterHealthResult:
        if not self._settings.enabled:
            return AdapterHealthResult(
                adapter_id=self.adapter_id(),
                status=AdapterHealthStatus.DEGRADED,
                message="disabled",
            )
        if self._state == PaperState.FAILED:
            return AdapterHealthResult(
                adapter_id=self.adapter_id(),
                status=AdapterHealthStatus.UNHEALTHY,
                message="failed",
            )
        return AdapterHealthResult(
            adapter_id=self.adapter_id(),
            status=AdapterHealthStatus.HEALTHY,
            message="ok",
        )

    def get_record(self, request_id: str) -> PaperExecutionRecord | None:
        with self._lock:
            return self._records.get(request_id)
