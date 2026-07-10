"""Feature validation contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class FeatureValidationResult(PlatformModel):
    """Outcome of feature validation."""

    valid: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: tuple[str, ...] = ()
