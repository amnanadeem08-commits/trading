"""Strategy builder domain exceptions."""

from __future__ import annotations

from models.common import PlatformError


class StrategyBuilderError(PlatformError):
    """Base error for deterministic strategy operations."""

    def __init__(self, message: str, *, code: str = "strategy_builder_error") -> None:
        super().__init__(message, code=code)


class StrategyValidationError(StrategyBuilderError):
    """Raised when a strategy definition violates its contract."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="strategy_validation_error")


class StrategyRegistrationError(StrategyBuilderError):
    """Raised when registration would violate registry invariants."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="strategy_registration_error")


class StrategyNotFoundError(StrategyBuilderError):
    """Raised when a requested strategy version is not registered."""

    def __init__(self, strategy_id: str, version: str) -> None:
        super().__init__(
            f"Strategy not found: {strategy_id}@{version}",
            code="strategy_not_found",
        )


class IndicatorEvaluationError(StrategyBuilderError):
    """Raised when indicator input is invalid or insufficient."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="indicator_evaluation_error")
