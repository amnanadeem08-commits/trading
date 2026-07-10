"""Common primitives shared across all domain contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlatformModel(BaseModel):
    """Base model for all platform contracts. Immutable by default."""

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        extra="forbid",
        populate_by_name=True,
    )


class PlatformError(Exception):
    """Base exception for all platform errors."""

    def __init__(self, message: str, *, code: str = "platform_error") -> None:
        self.code = code
        super().__init__(message)


class ConfigurationError(PlatformError):
    """Raised when configuration is missing or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="configuration_error")


class ContractViolationError(PlatformError):
    """Raised when a domain contract is violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="contract_violation")


UTCDateTime = Annotated[datetime, Field(description="Timezone-aware UTC datetime")]


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(UTC)


class VersionInfo(PlatformModel):
    """Version metadata for any versioned artifact."""

    version_id: str = Field(min_length=1, description="Unique version identifier")
    created_at: UTCDateTime = Field(default_factory=utc_now)
    description: str | None = None


class ReproducibilityKey(PlatformModel):
    """Identifies the exact artifact versions used to produce a decision."""

    feature_snapshot_version: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    strategy_version: str = Field(min_length=1)
    schema_version: str = Field(min_length=1)
    config_hash: str = Field(min_length=1, description="Hash of active config at decision time")

    @field_validator(
        "feature_snapshot_version",
        "model_version",
        "prompt_version",
        "strategy_version",
        "schema_version",
        "config_hash",
    )
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            msg = "Reproducibility key fields must not be empty"
            raise ValueError(msg)
        return stripped
