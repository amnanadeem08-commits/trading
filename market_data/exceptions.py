"""Market data framework exceptions."""

from __future__ import annotations

from models.common import PlatformError


class MarketDataError(PlatformError):
    """Base exception for market data framework errors."""

    def __init__(self, message: str, *, code: str = "market_data_error") -> None:
        super().__init__(message, code=code)


class MarketRecordNotFoundError(MarketDataError):
    """Raised when a market record cannot be resolved."""

    def __init__(self, record_id: str) -> None:
        self.record_id = record_id
        super().__init__(f"Market record not found: {record_id}", code="record_not_found")


class MarketRegistrationError(MarketDataError):
    """Raised when market registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="market_registration_error")


class MarketValidationError(MarketDataError):
    """Raised when market data validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="market_validation_error")


class MarketNormalizationError(MarketDataError):
    """Raised when normalization fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="market_normalization_error")


class StreamError(MarketDataError):
    """Raised when stream operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="stream_error")


class MarketVersionError(MarketDataError):
    """Raised when version operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="market_version_error")
