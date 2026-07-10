"""Confidence score contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class ConfidenceScore(PlatformModel):
    """Generic confidence score for risk assessment."""

    value: float = Field(ge=0.0, le=1.0, default=0.0)
    source: str = ""
    metadata: dict[str, str] = Field(default_factory=dict)
