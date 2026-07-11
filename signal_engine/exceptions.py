"""Signal engine package exceptions."""

from __future__ import annotations

from models.common import PlatformError


class SignalEngineError(PlatformError):
    """Base error for the signal engine package."""

    def __init__(self, message: str, *, code: str = "signal_engine_error") -> None:
        super().__init__(message, code=code)


class SignalAssemblyError(SignalEngineError):
    """Raised when a signal cannot be assembled from the provided inputs."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="signal_assembly_error")


class SignalNotFoundError(SignalEngineError):
    """Raised when a registered signal cannot be found."""

    def __init__(self, signal_id: str) -> None:
        super().__init__(f"Signal not found: {signal_id}", code="signal_not_found")
        self.signal_id = signal_id


class SignalRegistrationError(SignalEngineError):
    """Raised when signal registry registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="signal_registration_error")


class SignalIntakeError(SignalEngineError):
    """Raised when market/feature intake mapping fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="signal_intake_error")


class SignalRuleError(SignalEngineError):
    """Raised when a candidate rule cannot evaluate."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="signal_rule_error")


class SignalMLAttachmentError(SignalEngineError):
    """Raised when ML prediction cannot be attached to a signal request."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="signal_ml_attachment_error")


class SignalLLMAttachmentError(SignalEngineError):
    """Raised when LLM insight cannot be attached to a signal request."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="signal_llm_attachment_error")


class SignalRiskAttachmentError(SignalEngineError):
    """Raised when confidence, risk assessment, or invalidation cannot be bound."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="signal_risk_attachment_error")


class SignalValidationError(SignalEngineError):
    """Raised when a signal is explicitly rejected by validation."""

    def __init__(self, message: str, *, reasons: tuple[str, ...] = ()) -> None:
        detail = message if not reasons else f"{message}: {'; '.join(reasons)}"
        super().__init__(detail, code="signal_validation_error")
        self.reasons = reasons
