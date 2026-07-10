"""Connector validation result contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class ConnectorValidationResult(PlatformModel):
    """Outcome of connector validation checks."""

    valid: bool
    adapter_id: str = Field(min_length=1)
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: tuple[str, ...] = Field(default_factory=tuple)
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    version_compatible: bool = True
    capabilities_valid: bool = True
