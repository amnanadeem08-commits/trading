"""Registry for adapter-managed model sessions."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from framework_adapters.exceptions import AdapterNotFoundError
from framework_adapters.runtime.model_runtime_state import ModelRuntimeState
from framework_adapters.runtime.model_session_record import ModelSessionRecord
from ml_runtime.execution.model_executor import ModelExecutor
from models.common import utc_now


def build_model_session_key(
    *,
    model_id: str,
    artifact_id: str,
    adapter_id: str,
    model_version: str = "",
) -> str:
    """Build a deterministic cache key for a managed model session."""
    model = model_id.strip() or "default"
    artifact = artifact_id.strip() or "default"
    version = model_version.strip() or "default"
    return f"{model}:{artifact}:{adapter_id}:{version}"


class ModelSessionRegistry:
    """Tracks cached model sessions, executors, and reference counts."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, ModelSessionRecord] = {}
        self._executors: dict[str, ModelExecutor] = {}

    def register(
        self,
        *,
        session_key: str,
        record: ModelSessionRecord,
        executor: ModelExecutor,
    ) -> ModelSessionRecord:
        with self._lock:
            self._records[session_key] = record
            self._executors[session_key] = executor
            return record

    def lookup(self, session_key: str) -> ModelSessionRecord | None:
        with self._lock:
            return self._records.get(session_key)

    def get_executor(self, session_key: str) -> ModelExecutor:
        with self._lock:
            executor = self._executors.get(session_key)
            if executor is None:
                msg = f"model session executor not found: {session_key}"
                raise AdapterNotFoundError(msg)
            return executor

    def update(self, session_key: str, **updates: object) -> ModelSessionRecord:
        with self._lock:
            record = self._records.get(session_key)
            if record is None:
                msg = f"model session not found: {session_key}"
                raise AdapterNotFoundError(msg)
            updated = record.model_copy(update=updates)
            self._records[session_key] = updated
            return updated

    def increment_ref_count(self, session_key: str) -> ModelSessionRecord:
        with self._lock:
            record = self._records.get(session_key)
            if record is None:
                msg = f"model session not found: {session_key}"
                raise AdapterNotFoundError(msg)
            updated = record.model_copy(
                update={
                    "reference_count": record.reference_count + 1,
                    "last_access_at": utc_now(),
                    "cached": True,
                }
            )
            self._records[session_key] = updated
            return updated

    def decrement_ref_count(self, session_key: str) -> ModelSessionRecord:
        with self._lock:
            record = self._records.get(session_key)
            if record is None:
                msg = f"model session not found: {session_key}"
                raise AdapterNotFoundError(msg)
            updated = record.model_copy(
                update={"reference_count": max(0, record.reference_count - 1)}
            )
            self._records[session_key] = updated
            return updated

    def touch(self, session_key: str) -> ModelSessionRecord:
        with self._lock:
            record = self._records.get(session_key)
            if record is None:
                msg = f"model session not found: {session_key}"
                raise AdapterNotFoundError(msg)
            updated = record.model_copy(update={"last_access_at": utc_now()})
            self._records[session_key] = updated
            return updated

    def replace_executor(
        self,
        session_key: str,
        *,
        executor: ModelExecutor,
        record_updates: dict[str, object] | None = None,
    ) -> ModelSessionRecord:
        with self._lock:
            record = self._records.get(session_key)
            if record is None:
                msg = f"model session not found: {session_key}"
                raise AdapterNotFoundError(msg)
            self._executors[session_key] = executor
            updates = record_updates or {}
            updated = record.model_copy(update=updates)
            self._records[session_key] = updated
            return updated

    def remove(self, session_key: str) -> ModelSessionRecord | None:
        with self._lock:
            record = self._records.pop(session_key, None)
            self._executors.pop(session_key, None)
            return record

    def list_records(self) -> tuple[ModelSessionRecord, ...]:
        with self._lock:
            return tuple(self._records.values())

    def list_by_model_id(self, model_id: str) -> tuple[ModelSessionRecord, ...]:
        with self._lock:
            return tuple(record for record in self._records.values() if record.model_id == model_id)

    def list_by_state(self, state: ModelRuntimeState) -> tuple[ModelSessionRecord, ...]:
        with self._lock:
            return tuple(record for record in self._records.values() if record.state == state)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
            self._executors.clear()

    @staticmethod
    def new_session_id() -> str:
        return str(uuid4())
