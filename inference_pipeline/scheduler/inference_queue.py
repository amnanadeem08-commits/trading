"""Inference request queue."""

from __future__ import annotations

import time
from collections import deque
from threading import RLock

from inference_pipeline.exceptions import InferenceDispatchError, InferenceRequestNotFoundError
from inference_pipeline.requests.inference_request import InferenceRequest
from inference_pipeline.responses.inference_result import InferenceStatus
from models.common import PlatformModel


class QueuedInferenceRequest(PlatformModel):
    """Queued inference request with status tracking."""

    request: InferenceRequest
    status: InferenceStatus = InferenceStatus.QUEUED
    queued_at_ms: float = 0.0


class InferenceQueue:
    """Thread-safe FIFO queue for inference requests."""

    def __init__(self, *, max_size: int = 1000) -> None:
        self._lock = RLock()
        self._queue: deque[QueuedInferenceRequest] = deque()
        self._requests: dict[str, QueuedInferenceRequest] = {}
        self._max_size = max_size

    def enqueue(self, request: InferenceRequest) -> QueuedInferenceRequest:
        with self._lock:
            if len(self._queue) >= self._max_size:
                msg = f"Queue capacity ({self._max_size}) reached"
                raise InferenceDispatchError(msg)
            queued = QueuedInferenceRequest(
                request=request,
                status=InferenceStatus.QUEUED,
                queued_at_ms=time.monotonic() * 1000.0,
            )
            self._requests[request.request_id] = queued
            self._queue.append(queued)
        return queued

    def dequeue(self) -> QueuedInferenceRequest | None:
        with self._lock:
            if not self._queue:
                return None
            item = self._queue.popleft()
            running = item.model_copy(update={"status": InferenceStatus.RUNNING})
            self._requests[item.request.request_id] = running
            return running

    def peek(self) -> QueuedInferenceRequest | None:
        with self._lock:
            if not self._queue:
                return None
            return self._queue[0]

    def get(self, request_id: str) -> QueuedInferenceRequest:
        with self._lock:
            item = self._requests.get(request_id)
        if item is None:
            raise InferenceRequestNotFoundError(request_id)
        return item

    def update(self, request_id: str, *, status: InferenceStatus) -> None:
        with self._lock:
            item = self._requests.get(request_id)
            if item is not None:
                self._requests[request_id] = item.model_copy(update={"status": status})

    def size(self) -> int:
        with self._lock:
            return len(self._queue)

    def list_requests(self) -> tuple[QueuedInferenceRequest, ...]:
        with self._lock:
            return tuple(self._requests[rid] for rid in sorted(self._requests))
