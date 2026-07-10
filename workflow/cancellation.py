"""Workflow cancellation token."""

from __future__ import annotations

from threading import RLock


class CancellationToken:
    """Cancellation token for workflow execution."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._cancelled = False

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True

    def is_cancelled(self) -> bool:
        with self._lock:
            return self._cancelled
