"""Request context contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class RequestContext(PlatformModel):
    """Context describing an inbound platform request."""

    request_id: str = Field(min_length=1)
    source: str = Field(min_length=1, default="platform")
    initiated_at: UTCDateTime = Field(default_factory=utc_now)
    attributes: dict[str, str] = Field(default_factory=dict)
