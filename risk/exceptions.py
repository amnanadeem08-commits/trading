"""Risk layer exceptions."""

from __future__ import annotations

from models.common import PlatformError


class RiskError(PlatformError):
    """Base exception for risk layer errors."""

    def __init__(self, message: str, *, code: str = "risk_error") -> None:
        super().__init__(message, code=code)


class RiskNotFoundError(RiskError):
    """Raised when a requested risk engine is not registered."""

    def __init__(self, risk_id: str) -> None:
        super().__init__(f"Risk engine not found: {risk_id}", code="risk_not_found")
        self.risk_id = risk_id


class RiskRegistrationError(RiskError):
    """Raised when risk engine registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="risk_registration_error")


class RiskStateError(RiskError):
    """Raised when an invalid risk state transition is attempted."""

    def __init__(self, risk_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} risk '{risk_id}' in state '{current_state}'",
            code="risk_state_error",
        )
        self.risk_id = risk_id
        self.current_state = current_state
        self.operation = operation


class PolicyNotFoundError(RiskError):
    """Raised when a requested policy is not registered."""

    def __init__(self, policy_id: str) -> None:
        super().__init__(f"Policy not found: {policy_id}", code="policy_not_found")
        self.policy_id = policy_id


class PolicyRegistrationError(RiskError):
    """Raised when policy registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="policy_registration_error")


class ValidationError(RiskError):
    """Raised when validation operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class OrchestrationError(RiskError):
    """Raised when risk orchestration operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="orchestration_error")


class ScoringError(RiskError):
    """Raised when scoring operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="scoring_error")
