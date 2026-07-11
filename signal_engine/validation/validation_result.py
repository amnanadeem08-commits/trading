"""Signal validation result contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class SignalValidationResult(PlatformModel):
    """Accept/reject outcome for a signal validation pass."""

    signal_id: str = Field(min_length=1)
    passed: bool
    reasons: tuple[str, ...] = Field(default_factory=tuple)
    lifecycle_state: str = Field(min_length=1)
    validated_at: UTCDateTime = Field(default_factory=utc_now)
