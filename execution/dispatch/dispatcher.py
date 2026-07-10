"""Generic dispatch framework."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from execution.dispatch.dispatch_queue import DispatchQueue
from execution.dispatch.dispatch_request import DispatchRequest
from execution.dispatch.dispatch_result import DispatchResult
from execution.engine.execution_context import ExecutionContext
from execution.exceptions import DispatchError


class Dispatcher:
    """Prepares and records dispatch operations without external side effects."""

    def __init__(self, queue: DispatchQueue | None = None) -> None:
        self._lock = RLock()
        self._queue = queue or DispatchQueue()
        self._history: list[DispatchResult] = []

    @property
    def queue(self) -> DispatchQueue:
        """Return the underlying dispatch queue."""
        return self._queue

    def create_request(
        self,
        *,
        execution_id: str,
        engine_id: str,
        context: ExecutionContext,
        payload: dict[str, object] | None = None,
        priority: int = 0,
        request_id: str | None = None,
    ) -> DispatchRequest:
        """Build a dispatch request from execution context."""
        return DispatchRequest(
            request_id=request_id or str(uuid4()),
            execution_id=execution_id,
            engine_id=engine_id,
            context=context,
            payload=dict(payload or {}),
            priority=priority,
        )

    def enqueue(self, request: DispatchRequest) -> None:
        """Queue a dispatch request for later processing."""
        with self._lock:
            self._queue.enqueue(request)

    def dispatch(self, request: DispatchRequest) -> DispatchResult:
        """Record a dispatch operation without performing external actions."""
        with self._lock:
            result = DispatchResult(
                request_id=request.request_id,
                execution_id=request.execution_id,
                engine_id=request.engine_id,
                success=True,
                output={
                    "status": "recorded",
                    "payload_keys": sorted(request.payload.keys()),
                },
                metadata={
                    "dispatch_mode": "infrastructure",
                    "queue_size": str(self._queue.size()),
                },
            )
            self._history.append(result)
            return result

    def dispatch_next(self) -> DispatchResult:
        """Dequeue and dispatch the next request."""
        with self._lock:
            try:
                request = self._queue.dequeue()
            except Exception as exc:
                raise DispatchError("No dispatch request available") from exc
            return self.dispatch(request)

    def history(self) -> list[DispatchResult]:
        """Return recorded dispatch results."""
        with self._lock:
            return list(self._history)

    def reset(self) -> None:
        """Clear queue and dispatch history."""
        with self._lock:
            self._queue.clear()
            self._history.clear()
