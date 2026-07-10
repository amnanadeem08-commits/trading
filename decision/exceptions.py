"""Decision layer exceptions."""

from __future__ import annotations

from models.common import PlatformError


class DecisionError(PlatformError):
    """Base exception for decision layer errors."""

    def __init__(self, message: str, *, code: str = "decision_error") -> None:
        super().__init__(message, code=code)


class DecisionNotFoundError(DecisionError):
    """Raised when a requested decision engine is not registered."""

    def __init__(self, decision_id: str) -> None:
        super().__init__(f"Decision engine not found: {decision_id}", code="decision_not_found")
        self.decision_id = decision_id


class DecisionRegistrationError(DecisionError):
    """Raised when decision engine registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="decision_registration_error")


class DecisionStateError(DecisionError):
    """Raised when an invalid decision state transition is attempted."""

    def __init__(self, decision_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} decision '{decision_id}' in state '{current_state}'",
            code="decision_state_error",
        )
        self.decision_id = decision_id
        self.current_state = current_state
        self.operation = operation


class PolicyNotFoundError(DecisionError):
    """Raised when a requested policy is not registered."""

    def __init__(self, policy_id: str) -> None:
        super().__init__(f"Policy not found: {policy_id}", code="policy_not_found")
        self.policy_id = policy_id


class PolicyRegistrationError(DecisionError):
    """Raised when policy registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="policy_registration_error")


class OrchestrationError(DecisionError):
    """Raised when decision orchestration operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="orchestration_error")


class EvaluationError(DecisionError):
    """Raised when decision evaluation operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="evaluation_error")
