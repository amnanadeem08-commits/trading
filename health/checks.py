"""Startup and shutdown health checks."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import Field

from models.common import PlatformModel


class CheckOutcome(StrEnum):
    """Result of a startup or shutdown check."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CheckResult(PlatformModel):
    """Result of a single lifecycle check."""

    name: str = Field(min_length=1)
    outcome: CheckOutcome
    message: str = Field(min_length=1)
    duration_ms: float = Field(ge=0, default=0)


class LifecycleCheck(ABC):
    """Interface for startup and shutdown checks."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the check name."""

    @abstractmethod
    def run(self) -> CheckResult:
        """Execute the check and return the result."""


class StartupCheck(LifecycleCheck):
    """Startup lifecycle check."""

    @abstractmethod
    def run(self) -> CheckResult:
        """Execute startup check."""


class ShutdownCheck(LifecycleCheck):
    """Shutdown lifecycle check."""

    @abstractmethod
    def run(self) -> CheckResult:
        """Execute shutdown check."""
