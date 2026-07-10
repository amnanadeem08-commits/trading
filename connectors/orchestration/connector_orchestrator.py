"""Connector orchestrator."""

from __future__ import annotations

from connectors.adapters.adapter_context import AdapterContext
from connectors.adapters.adapter_metadata import AdapterState
from connectors.adapters.adapter_registry import AdapterRegistry
from connectors.adapters.execution_adapter import ExecutionAdapter
from connectors.dispatch.dispatch_bridge import DispatchBridge
from connectors.dispatch.dispatch_response import DispatchResponse
from connectors.exceptions import AdapterNotFoundError, ConnectorOrchestrationError
from connectors.lifecycle.connector_lifecycle import (
    ConnectorLifecycleEventType,
    ConnectorLifecycleManager,
)
from connectors.registry.connector_registry import ConnectorRegistry
from connectors.validation.connector_validator import ConnectorValidator
from execution.dispatch.dispatch_request import DispatchRequest


class ConnectorOrchestrator:
    """Coordinates connector flow: validation -> initialize -> dispatch -> shutdown."""

    def __init__(
        self,
        *,
        connector_registry: ConnectorRegistry | None = None,
        adapter_registry: AdapterRegistry | None = None,
        validator: ConnectorValidator | None = None,
        bridge: DispatchBridge | None = None,
        lifecycle: ConnectorLifecycleManager | None = None,
    ) -> None:
        self._connectors = connector_registry or ConnectorRegistry()
        self._adapters = adapter_registry or self._connectors.adapters
        self._validator = validator or ConnectorValidator()
        self._bridge = bridge or DispatchBridge(adapter_registry=self._adapters)
        self._lifecycle = lifecycle

    def register_connector(
        self,
        *,
        connector_id: str,
        adapter_id: str,
        name: str,
        version: str,
        correlation_id: str,
        trace_id: str,
    ) -> None:
        """Register a connector and emit lifecycle event."""
        from connectors.registry.connector_registry import ConnectorRecord

        record = ConnectorRecord(
            connector_id=connector_id,
            adapter_id=adapter_id,
            name=name,
            version=version,
        )
        self._connectors.register(record)
        self._emit_lifecycle(
            ConnectorLifecycleEventType.CONNECTOR_REGISTERED,
            connector_id=connector_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="connector registered",
        )

    def dispatch(
        self,
        request: DispatchRequest,
        adapter: ExecutionAdapter,
        *,
        connector_id: str,
        required_capabilities: tuple[str, ...] = ("dispatch",),
    ) -> DispatchResponse:
        """Execute connector pipeline: validate -> initialize -> dispatch."""
        adapter_id = adapter.adapter_id()
        if not self._adapters.exists(adapter_id):
            raise AdapterNotFoundError(adapter_id)

        correlation_id = request.context.correlation_id
        trace_id = request.context.trace_id

        self._emit_lifecycle(
            ConnectorLifecycleEventType.CONNECTOR_DISPATCH_REQUESTED,
            connector_id=connector_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message="dispatch requested",
            payload={"request_id": request.request_id},
        )

        try:
            metadata = self._adapters.resolve(adapter_id)
            validation_result = self._validator.validate(
                adapter_id=adapter_id,
                metadata=metadata,
                required_capabilities=required_capabilities,
            )
            self._emit_lifecycle(
                ConnectorLifecycleEventType.CONNECTOR_VALIDATED,
                connector_id=connector_id,
                correlation_id=correlation_id,
                trace_id=trace_id,
                message="connector validated",
                payload={"valid": validation_result.valid},
            )
            if not validation_result.valid:
                self._adapters.set_state(adapter_id, AdapterState.FAILED)
                return DispatchResponse(
                    request_id=request.request_id,
                    execution_id=request.execution_id,
                    adapter_id=adapter_id,
                    success=False,
                    output={"failed": True, "reason": "validation_failed"},
                    error_message="; ".join(validation_result.errors),
                )

            context = AdapterContext(
                adapter_id=adapter_id,
                correlation_id=correlation_id,
                trace_id=trace_id,
                execution_id=request.execution_id,
                request_id=request.request_id,
                execution_context=request.context,
                payload=dict(request.payload),
            )
            adapter.initialize(context)
            self._adapters.set_state(adapter_id, AdapterState.INITIALIZED)
            if self._connectors.exists(connector_id):
                self._connectors.set_state(connector_id, AdapterState.INITIALIZED)
            self._emit_lifecycle(
                ConnectorLifecycleEventType.CONNECTOR_INITIALIZED,
                connector_id=connector_id,
                correlation_id=correlation_id,
                trace_id=trace_id,
                message="connector initialized",
            )

            self._adapters.set_state(adapter_id, AdapterState.VALIDATED)
            connector_request = self._bridge.wrap_request(request, adapter_id=adapter_id)
            response = self._bridge.route(connector_request, adapter)
            self._adapters.set_state(adapter_id, AdapterState.ACTIVE)
            return response
        except AdapterNotFoundError:
            raise
        except Exception as error:
            self._adapters.set_state(adapter_id, AdapterState.FAILED)
            msg = f"Connector orchestration failed: {error}"
            raise ConnectorOrchestrationError(msg) from error

    def shutdown(
        self,
        adapter: ExecutionAdapter,
        *,
        connector_id: str,
        request: DispatchRequest,
    ) -> None:
        """Shut down an adapter and emit lifecycle event."""
        adapter_id = adapter.adapter_id()
        context = AdapterContext(
            adapter_id=adapter_id,
            correlation_id=request.context.correlation_id,
            trace_id=request.context.trace_id,
            execution_id=request.execution_id,
            request_id=request.request_id,
            execution_context=request.context,
        )
        adapter.shutdown(context)
        self._adapters.set_state(adapter_id, AdapterState.SHUTDOWN)
        if self._connectors.exists(connector_id):
            self._connectors.set_state(connector_id, AdapterState.SHUTDOWN)
        self._emit_lifecycle(
            ConnectorLifecycleEventType.CONNECTOR_SHUTDOWN,
            connector_id=connector_id,
            correlation_id=request.context.correlation_id,
            trace_id=request.context.trace_id,
            message="connector shutdown",
        )

    def _emit_lifecycle(
        self,
        event_type: ConnectorLifecycleEventType,
        *,
        connector_id: str,
        correlation_id: str,
        trace_id: str,
        message: str,
        payload: dict[str, object] | None = None,
    ) -> None:
        if self._lifecycle is None:
            return
        self._lifecycle.emit(
            event_type,
            connector_id=connector_id,
            correlation_id=correlation_id,
            trace_id=trace_id,
            message=message,
            payload=payload,
        )
