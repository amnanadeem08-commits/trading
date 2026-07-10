"""Heartbeat service scaffold."""

from __future__ import annotations

from threading import RLock

from health.models import HealthState
from models.common import UTCDateTime, utc_now


class HeartbeatService:
    """Tracks service heartbeat timestamps."""

    def __init__(self, interval_seconds: int) -> None:
        self._interval_seconds = interval_seconds
        self._lock = RLock()
        self._last_beat: UTCDateTime | None = None

    @property
    def interval_seconds(self) -> int:
        return self._interval_seconds

    def beat(self) -> UTCDateTime:
        """Record a heartbeat."""
        timestamp = utc_now()
        with self._lock:
            self._last_beat = timestamp
        return timestamp

    def last_beat(self) -> UTCDateTime | None:
        with self._lock:
            return self._last_beat

    def is_alive(self) -> bool:
        """Return whether heartbeat is within interval."""
        with self._lock:
            if self._last_beat is None:
                return False
            elapsed = (utc_now() - self._last_beat).total_seconds()
            return elapsed <= self._interval_seconds

    def status(self) -> HealthState:
        return HealthState.HEALTHY if self.is_alive() else HealthState.UNHEALTHY
