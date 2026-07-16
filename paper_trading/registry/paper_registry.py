"""In-memory registry for paper trading sessions."""

from __future__ import annotations

from threading import RLock

from paper_trading.contracts.paper_request import (
    PaperOrchestrationResult,
    PaperSessionStatus,
)
from paper_trading.exceptions import PaperRegistrationError, PaperSessionNotFoundError
from paper_trading.registry.paper_record import PaperSessionRecord

_default_paper_registry: PaperSessionRegistry | None = None
_registry_lock = RLock()


class PaperSessionRegistry:
    """Thread-safe registry for paper trading sessions."""

    def __init__(self, *, max_sessions: int = 10_000) -> None:
        if max_sessions < 1:
            msg = "max_sessions must be >= 1"
            raise PaperRegistrationError(msg)
        self._lock = RLock()
        self._max_sessions = max_sessions
        self._records: dict[str, PaperSessionRecord] = {}

    def register(self, result: PaperOrchestrationResult) -> PaperSessionRecord:
        """Register an orchestration result. Duplicate session ids are rejected."""
        session_id = result.session_id
        with self._lock:
            if session_id in self._records:
                msg = f"Paper session already registered: {session_id}"
                raise PaperRegistrationError(msg)
            if len(self._records) >= self._max_sessions:
                msg = f"Paper session registry capacity exceeded: {self._max_sessions}"
                raise PaperRegistrationError(msg)
            record = PaperSessionRecord(
                session_id=session_id,
                signal_id=result.signal_id,
                status=result.status,
                result=result,
            )
            self._records[session_id] = record
            return record

    def get(self, session_id: str) -> PaperSessionRecord:
        with self._lock:
            record = self._records.get(session_id)
            if record is None:
                raise PaperSessionNotFoundError(session_id)
            return record

    def update_status(
        self,
        session_id: str,
        *,
        status: PaperSessionStatus,
        message: str,
        risk_gate_reasons: tuple[str, ...] = (),
    ) -> PaperSessionRecord:
        """Update an existing session status (append-only ledgers remain untouched).

        This is used for PAPER-005 cancellation events before any fill/ledger
        mutations occur.
        """
        with self._lock:
            record = self._records.get(session_id)
            if record is None:
                raise PaperSessionNotFoundError(session_id)

            updated_result = record.result.model_copy(
                update={
                    "status": status,
                    "message": message,
                    "risk_gate_reasons": risk_gate_reasons,
                }
            )
            updated = record.model_copy(update={"status": status, "result": updated_result})
            self._records[session_id] = updated
            return updated

    def list_ids(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._records))

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._records)


def get_paper_registry() -> PaperSessionRegistry:
    """Return the process-wide default paper session registry."""
    global _default_paper_registry
    with _registry_lock:
        if _default_paper_registry is None:
            _default_paper_registry = PaperSessionRegistry()
        return _default_paper_registry


def reset_paper_registry() -> None:
    """Reset the process-wide default paper session registry."""
    global _default_paper_registry
    with _registry_lock:
        _default_paper_registry = None
