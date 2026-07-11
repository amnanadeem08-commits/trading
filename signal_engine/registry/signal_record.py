"""Registry record for assembled signals."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from models.signal import ExplainableSignal


class SignalRecord(PlatformModel):
    """Stored signal engine registry entry."""

    signal_id: str = Field(min_length=1)
    signal: ExplainableSignal
    registered_at: UTCDateTime = Field(default_factory=utc_now)
