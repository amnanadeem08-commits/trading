"""Validation result contracts."""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel, UTCDateTime, utc_now


class ValidationState(StrEnum):
    """Lifecycle states for validation operations."""

    CREATED = "created"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"


class ValidationResult(PlatformModel):
    """Outcome of a validation pipeline execution."""

    validation_id: str = Field(min_length=1)
    state: ValidationState = ValidationState.PASSED
    passed_rules: tuple[str, ...] = Field(default_factory=tuple)
    failed_rules: tuple[str, ...] = Field(default_factory=tuple)
    metadata: dict[str, str] = Field(default_factory=dict)
    completed_at: UTCDateTime = Field(default_factory=utc_now)

    @property
    def passed(self) -> bool:
        """Return whether all rules passed."""
        return self.state == ValidationState.PASSED and not self.failed_rules
