"""Adapter registry."""

from __future__ import annotations

from threading import RLock

from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.exceptions import AdapterNotFoundError
from framework_adapters.registry.adapter_record import AdapterRecord, AdapterState
from models.common import utc_now


class AdapterRegistry:
    """Thread-safe registry for framework adapters with multi-adapter support."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._adapters: dict[str, FrameworkAdapter] = {}
        self._records: dict[str, AdapterRecord] = {}
        self._engine_index: dict[EngineType, list[str]] = {}
        self._default_adapter_id: str | None = None

    def register(self, adapter: FrameworkAdapter, *, priority: int = 0) -> AdapterRecord:
        adapter_id = adapter.adapter_id()
        metadata = adapter.metadata()
        manifest = adapter.manifest()
        manifest_priority = priority
        raw_priority = manifest.attributes.get("priority")
        if isinstance(raw_priority, int):
            manifest_priority = raw_priority
        now = utc_now()
        record = AdapterRecord(
            adapter_id=adapter_id,
            metadata=metadata,
            manifest=manifest,
            state=AdapterState.REGISTERED,
            priority=manifest_priority,
            registered_at=now,
            updated_at=now,
        )
        engine_type = adapter.engine_type()
        with self._lock:
            self._adapters[adapter_id] = adapter
            self._records[adapter_id] = record
            engine_entries = self._engine_index.setdefault(engine_type, [])
            if adapter_id not in engine_entries:
                engine_entries.append(adapter_id)
            engine_entries.sort(
                key=lambda entry_id: self._records[entry_id].priority,
                reverse=True,
            )
        return record

    def lookup(self, adapter_id: str) -> AdapterRecord:
        with self._lock:
            record = self._records.get(adapter_id)
        if record is None:
            raise AdapterNotFoundError(adapter_id)
        return record

    def get_adapter(self, adapter_id: str) -> FrameworkAdapter:
        with self._lock:
            adapter = self._adapters.get(adapter_id)
        if adapter is None:
            raise AdapterNotFoundError(adapter_id)
        return adapter

    def list(self) -> tuple[AdapterRecord, ...]:
        with self._lock:
            return tuple(self._records[aid] for aid in sorted(self._records))

    def list_by_engine_type(self, engine_type: EngineType) -> tuple[AdapterRecord, ...]:
        with self._lock:
            adapter_ids = self._engine_index.get(engine_type, [])
            return tuple(
                self._records[adapter_id]
                for adapter_id in adapter_ids
                if adapter_id in self._records
            )

    def set_default_adapter(self, adapter_id: str) -> None:
        with self._lock:
            if adapter_id not in self._records:
                raise AdapterNotFoundError(adapter_id)
            self._default_adapter_id = adapter_id

    def get_default_adapter_id(self) -> str | None:
        with self._lock:
            return self._default_adapter_id

    def update_state(self, adapter_id: str, state: AdapterState) -> AdapterRecord:
        with self._lock:
            record = self._records.get(adapter_id)
            if record is None:
                raise AdapterNotFoundError(adapter_id)
            updated = record.model_copy(update={"state": state, "updated_at": utc_now()})
            self._records[adapter_id] = updated
            return updated

    def unregister(self, adapter_id: str) -> None:
        with self._lock:
            record = self._records.pop(adapter_id, None)
            self._adapters.pop(adapter_id, None)
            if record is None:
                raise AdapterNotFoundError(adapter_id)
            engine_entries = self._engine_index.get(record.metadata.engine_type, [])
            if adapter_id in engine_entries:
                engine_entries.remove(adapter_id)
            if self._default_adapter_id == adapter_id:
                self._default_adapter_id = None

    def clear(self) -> None:
        with self._lock:
            self._adapters.clear()
            self._records.clear()
            self._engine_index.clear()
            self._default_adapter_id = None
