"""Inference registry."""

from __future__ import annotations

from threading import RLock

from inference_pipeline.exceptions import InferenceRequestNotFoundError
from inference_pipeline.responses.inference_metadata import InferenceMetadata
from inference_pipeline.responses.inference_result import InferenceResult, InferenceStatus
from models.common import PlatformModel, UTCDateTime, utc_now


class InferenceRegistryEntry(PlatformModel):
    """Indexed inference request record."""

    request_id: str
    model_id: str
    status: InferenceStatus
    metadata: InferenceMetadata | None
    registered_at: UTCDateTime
    updated_at: UTCDateTime


class InferenceRegistry:
    """Thread-safe registry for inference request history."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, InferenceRegistryEntry] = {}
        self._history: dict[str, tuple[str, ...]] = {}

    def register(self, result: InferenceResult) -> InferenceRegistryEntry:
        now = utc_now()
        model_id = result.metadata.model_id if result.metadata else ""
        entry = InferenceRegistryEntry(
            request_id=result.request_id,
            model_id=model_id,
            status=result.status,
            metadata=result.metadata,
            registered_at=now,
            updated_at=now,
        )
        with self._lock:
            self._entries[result.request_id] = entry
            if model_id:
                model_history = self._history.get(model_id, ())
                if result.request_id not in model_history:
                    self._history[model_id] = (*model_history, result.request_id)
        return entry

    def lookup(self, request_id: str) -> InferenceRegistryEntry:
        with self._lock:
            entry = self._entries.get(request_id)
        if entry is None:
            raise InferenceRequestNotFoundError(request_id)
        return entry

    def history(self, model_id: str) -> tuple[InferenceRegistryEntry, ...]:
        with self._lock:
            request_ids = self._history.get(model_id, ())
            return tuple(self._entries[rid] for rid in request_ids if rid in self._entries)

    def latest(self, model_id: str) -> InferenceRegistryEntry | None:
        entries = self.history(model_id)
        if not entries:
            return None
        return entries[-1]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._history.clear()

    def update(self, result: InferenceResult) -> InferenceRegistryEntry:
        with self._lock:
            existing = self._entries.get(result.request_id)
            if existing is None:
                return self.register(result)
            entry = existing.model_copy(
                update={
                    "status": result.status,
                    "metadata": result.metadata,
                    "updated_at": utc_now(),
                }
            )
            self._entries[result.request_id] = entry
            return entry
