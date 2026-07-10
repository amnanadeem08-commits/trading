"""Approval score contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class ApprovalScore(PlatformModel):
    """Generic approval score for risk assessment."""

    value: float = Field(ge=0.0, le=1.0, default=0.0)
    approved: bool = True
    metadata: dict[str, str] = Field(default_factory=dict)
