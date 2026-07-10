"""Simulation timestamp utilities."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from models.common import UTCDateTime, utc_now


class SimulationClock:
    """Provides timestamps for simulated execution operations."""

    def now(self) -> UTCDateTime:
        """Return the current UTC timestamp."""
        return utc_now()

    def advance(self, *, base: UTCDateTime, milliseconds: int) -> UTCDateTime:
        """Return a timestamp advanced by the given number of milliseconds."""
        if milliseconds <= 0:
            return base
        advanced = base + timedelta(milliseconds=milliseconds / 1000)
        if isinstance(advanced, datetime):
            return advanced.replace(tzinfo=UTC) if advanced.tzinfo is None else advanced
        return advanced
