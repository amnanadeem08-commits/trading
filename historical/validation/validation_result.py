"""Historical validation result contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class HistoricalValidationResult(PlatformModel):
    """Outcome of historical validation checks."""

    valid: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: tuple[str, ...] = ()
