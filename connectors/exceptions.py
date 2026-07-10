"""Connector layer typed exceptions."""

from __future__ import annotations

from models.common import PlatformError


class ConnectorError(PlatformError):
    """Base exception for all connector-layer errors."""

    def __init__(self, message: str, *, market_id: str | None = None) -> None:
        self.market_id = market_id
        super().__init__(message, code="connector_error")


class AuthenticationError(ConnectorError):
    """Raised when connector authentication fails."""

    def __init__(self, message: str, *, market_id: str | None = None) -> None:
        super().__init__(message, market_id=market_id)
        self.code = "connector_authentication_error"


class ConnectionError(ConnectorError):
    """Raised when a connector cannot establish or maintain a connection."""

    def __init__(self, message: str, *, market_id: str | None = None) -> None:
        super().__init__(message, market_id=market_id)
        self.code = "connector_connection_error"


class RateLimitError(ConnectorError):
    """Raised when a connector hits provider rate limits."""

    def __init__(
        self,
        message: str,
        *,
        market_id: str | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(message, market_id=market_id)
        self.code = "connector_rate_limit_error"


class UnsupportedCapabilityError(ConnectorError):
    """Raised when a connector does not support the requested capability."""

    def __init__(
        self, message: str, *, market_id: str | None = None, capability: str | None = None
    ) -> None:
        self.capability = capability
        super().__init__(message, market_id=market_id)
        self.code = "connector_unsupported_capability"


class NormalizationError(ConnectorError):
    """Raised when raw market data cannot be normalized."""

    def __init__(
        self, message: str, *, market_id: str | None = None, field: str | None = None
    ) -> None:
        self.field = field
        super().__init__(message, market_id=market_id)
        self.code = "connector_normalization_error"


class ConnectorNotFoundError(ConnectorError):
    """Raised when a connector is not registered."""

    def __init__(self, message: str, *, market_id: str | None = None) -> None:
        super().__init__(message, market_id=market_id)
        self.code = "connector_not_found"


class AdapterNotFoundError(ConnectorError):
    """Raised when an execution adapter is not registered."""

    def __init__(self, adapter_id: str) -> None:
        super().__init__(f"Adapter not found: {adapter_id}", market_id=None)
        self.adapter_id = adapter_id
        self.code = "adapter_not_found"


class AdapterRegistrationError(ConnectorError):
    """Raised when adapter registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, market_id=None)
        self.code = "adapter_registration_error"


class AdapterStateError(ConnectorError):
    """Raised when an invalid adapter state transition is attempted."""

    def __init__(self, adapter_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} adapter '{adapter_id}' in state '{current_state}'",
            market_id=None,
        )
        self.adapter_id = adapter_id
        self.current_state = current_state
        self.operation = operation
        self.code = "adapter_state_error"


class DispatchBridgeError(ConnectorError):
    """Raised when dispatch bridge operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, market_id=None)
        self.code = "dispatch_bridge_error"


class ConnectorValidationError(ConnectorError):
    """Raised when connector validation operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, market_id=None)
        self.code = "connector_validation_error"


class ConnectorOrchestrationError(ConnectorError):
    """Raised when connector orchestration operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, market_id=None)
        self.code = "connector_orchestration_error"
