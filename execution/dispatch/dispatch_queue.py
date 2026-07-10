"""In-memory dispatch queue."""

from __future__ import annotations

from threading import RLock

from execution.dispatch.dispatch_request import DispatchRequest
from execution.exceptions import QueueError


class DispatchQueue:
    """Thread-safe in-memory queue for dispatch requests."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._items: list[DispatchRequest] = []

    def enqueue(self, request: DispatchRequest) -> None:
        """Add a dispatch request to the queue."""
        with self._lock:
            self._items.append(request)
            self._items.sort(key=lambda item: (-item.priority, item.created_at))

    def dequeue(self) -> DispatchRequest:
        """Remove and return the highest-priority dispatch request."""
        with self._lock:
            if not self._items:
                raise QueueError("Dispatch queue is empty")
            return self._items.pop(0)

    def peek(self) -> DispatchRequest | None:
        """Return the next dispatch request without removing it."""
        with self._lock:
            if not self._items:
                return None
            return self._items[0]

    def size(self) -> int:
        """Return the number of queued dispatch requests."""
        with self._lock:
            return len(self._items)

    def clear(self) -> None:
        """Remove all queued dispatch requests."""
        with self._lock:
            self._items.clear()

    def list_all(self) -> list[DispatchRequest]:
        """Return a snapshot of all queued requests."""
        with self._lock:
            return list(self._items)
