"""Dispatch bridge for routing execution requests to adapters."""

from __future__ import annotations

from threading import RLock

from connectors.adapters.adapter_context import AdapterContext
from connectors.adapters.adapter_registry import AdapterRegistry
from connectors.adapters.execution_adapter import ExecutionAdapter
from connectors.dispatch.dispatch_request import ConnectorDispatchRequest
from connectors.dispatch.dispatch_response import DispatchResponse
from connectors.exceptions import AdapterNotFoundError, DispatchBridgeError
from execution.dispatch.dispatch_request import DispatchRequest


class DispatchBridge:
    """Routes dispatch requests to registered adapters without external side effects."""

    def __init__(self, *, adapter_registry: AdapterRegistry | None = None) -> None:
        self._lock = RLock()
        self._registry = adapter_registry or AdapterRegistry()
        self._history: list[DispatchResponse] = []

    @property
    def registry(self) -> AdapterRegistry:
        """Return the underlying adapter registry."""
        return self._registry

    def wrap_request(
        self,
        request: DispatchRequest,
        *,
        adapter_id: str,
    ) -> ConnectorDispatchRequest:
        """Wrap an execution dispatch request for connector routing."""
        return ConnectorDispatchRequest(adapter_id=adapter_id, request=request)

    def route(
        self,
        connector_request: ConnectorDispatchRequest,
        adapter: ExecutionAdapter,
    ) -> DispatchResponse:
        """Route a dispatch request to the given adapter."""
        request = connector_request.request
        adapter_id = connector_request.adapter_id
        if not self._registry.exists(adapter_id):
            raise AdapterNotFoundError(adapter_id)

        context = AdapterContext(
            adapter_id=adapter_id,
            correlation_id=request.context.correlation_id,
            trace_id=request.context.trace_id,
            execution_id=request.execution_id,
            request_id=request.request_id,
            execution_context=request.context,
            payload=dict(request.payload),
        )

        with self._lock:
            try:
                if not adapter.validate(context):
                    raise DispatchBridgeError("Adapter validation failed")
                output = adapter.dispatch(context)
                result = DispatchResponse(
                    request_id=request.request_id,
                    execution_id=request.execution_id,
                    adapter_id=adapter_id,
                    success=True,
                    output=output,
                    metadata={"bridge_mode": "infrastructure"},
                )
            except DispatchBridgeError:
                raise
            except Exception as error:
                result = DispatchResponse(
                    request_id=request.request_id,
                    execution_id=request.execution_id,
                    adapter_id=adapter_id,
                    success=False,
                    output={},
                    error_message=str(error),
                    metadata={"bridge_mode": "infrastructure"},
                )
            self._history.append(result)
            return result

    def history(self) -> list[DispatchResponse]:
        """Return recorded dispatch responses."""
        with self._lock:
            return list(self._history)

    def reset(self) -> None:
        """Clear dispatch history."""
        with self._lock:
            self._history.clear()
