"""Runtime session management."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from ml_runtime.exceptions import RuntimeSessionError
from ml_runtime.execution.execution_result import ExecutionResult, ExecutionStatus
from ml_runtime.runtime.runtime_context import RuntimeContext
from models.common import PlatformModel, UTCDateTime, utc_now


class RuntimeSession(PlatformModel):
    """Tracks a single ML runtime execution session."""

    session_id: str
    request_id: str
    model_id: str
    executor_id: str
    status: ExecutionStatus
    created_at: UTCDateTime
    updated_at: UTCDateTime
    result: ExecutionResult | None = None


class RuntimeSessionManager:
    """Thread-safe session manager for ML runtime."""

    def __init__(self, *, max_sessions: int = 100) -> None:
        self._lock = RLock()
        self._sessions: dict[str, RuntimeSession] = {}
        self._max_sessions = max_sessions

    def create(
        self,
        *,
        request_id: str,
        model_id: str,
        executor_id: str,
    ) -> RuntimeSession:
        now = utc_now()
        session = RuntimeSession(
            session_id=f"session-{uuid4()}",
            request_id=request_id,
            model_id=model_id,
            executor_id=executor_id,
            status=ExecutionStatus.PENDING,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            if len(self._sessions) >= self._max_sessions:
                msg = "Maximum runtime sessions exceeded"
                raise RuntimeSessionError(msg)
            self._sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> RuntimeSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            msg = f"Runtime session not found: {session_id}"
            raise RuntimeSessionError(msg)
        return session

    def update(
        self, session_id: str, *, status: ExecutionStatus, result: ExecutionResult | None = None
    ) -> RuntimeSession:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                msg = f"Runtime session not found: {session_id}"
                raise RuntimeSessionError(msg)
            updated = session.model_copy(
                update={
                    "status": status,
                    "result": result,
                    "updated_at": utc_now(),
                }
            )
            self._sessions[session_id] = updated
            return updated

    def build_context(
        self,
        session: RuntimeSession,
        *,
        input_metadata: dict[str, object],
        model_version: str,
        artifact_reference: str,
        config_hash: str = "",
        checksum: str = "",
        correlation_id: str = "",
        trace_id: str = "",
    ) -> RuntimeContext:
        return RuntimeContext(
            session_id=session.session_id,
            request_id=session.request_id,
            model_id=session.model_id,
            model_version=model_version,
            artifact_reference=artifact_reference,
            executor_id=session.executor_id,
            input_metadata=input_metadata,
            correlation_id=correlation_id,
            trace_id=trace_id,
            config_hash=config_hash,
            checksum=checksum,
        )

    def clear(self) -> None:
        with self._lock:
            self._sessions.clear()

    def list_sessions(self) -> tuple[RuntimeSession, ...]:
        with self._lock:
            return tuple(self._sessions[sid] for sid in sorted(self._sessions))
