"""Paper trading package exceptions."""

from __future__ import annotations

from models.common import PlatformError


class PaperTradingError(PlatformError):
    """Base error for the paper trading package."""

    def __init__(self, message: str, *, code: str = "paper_trading_error") -> None:
        super().__init__(message, code=code)


class PaperOrchestrationError(PaperTradingError):
    """Raised when paper orchestration cannot proceed."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="paper_orchestration_error")


class PaperRegistrationError(PaperTradingError):
    """Raised when paper session registry registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="paper_registration_error")


class PaperSessionNotFoundError(PaperTradingError):
    """Raised when a paper session cannot be found."""

    def __init__(self, session_id: str) -> None:
        super().__init__(
            f"Paper session not found: {session_id}",
            code="paper_session_not_found",
        )
        self.session_id = session_id


class PaperLiveTradingDisabledError(PaperTradingError):
    """Raised when live trading is enabled — paper path refuses to continue."""

    def __init__(self) -> None:
        super().__init__(
            "Live trading is enabled; paper trading path refuses to run "
            "(broker automation remains gated)",
            code="paper_live_trading_refused",
        )


class PaperMappingError(PaperTradingError):
    """Raised when a signal cannot be mapped to a paper order request."""

    def __init__(self, message: str, *, reasons: tuple[str, ...] = ()) -> None:
        detail = message if not reasons else f"{message}: {'; '.join(reasons)}"
        super().__init__(detail, code="paper_mapping_error")
        self.reasons = reasons


class PaperRiskRejectedError(PaperTradingError):
    """Raised when the pre-fill risk gate rejects (fail closed)."""

    def __init__(self, message: str, *, reasons: tuple[str, ...] = ()) -> None:
        detail = message if not reasons else f"{message}: {'; '.join(reasons)}"
        super().__init__(detail, code="paper_risk_rejected")
        self.reasons = reasons


class PaperJournalNotFoundError(PaperTradingError):
    """Raised when a journal entry cannot be found."""

    def __init__(self, journal_id: str) -> None:
        super().__init__(
            f"Paper journal entry not found: {journal_id}",
            code="paper_journal_not_found",
        )
        self.journal_id = journal_id
