"""Registry record for paper trading sessions."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now
from paper_trading.contracts.paper_request import (
    PaperOrchestrationResult,
    PaperSessionStatus,
)


class PaperSessionRecord(PlatformModel):
    """Stored paper trading session entry."""

    session_id: str = Field(min_length=1)
    signal_id: str = Field(min_length=1)
    status: PaperSessionStatus
    result: PaperOrchestrationResult
    registered_at: UTCDateTime = Field(default_factory=utc_now)
