"""Feature store validation result."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class ValidationResult(PlatformModel):
    """Outcome of feature store validation."""

    valid: bool
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: tuple[str, ...] = ()
