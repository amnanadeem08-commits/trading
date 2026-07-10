"""Execution validation result contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class ExecutionValidationResult(PlatformModel):
    """Outcome of execution validation checks."""

    valid: bool
    execution_id: str = Field(min_length=1)
    checks: dict[str, bool] = Field(default_factory=dict)
    errors: tuple[str, ...] = Field(default_factory=tuple)
    warnings: tuple[str, ...] = Field(default_factory=tuple)
    version_compatible: bool = True
    policy_compliant: bool = True
