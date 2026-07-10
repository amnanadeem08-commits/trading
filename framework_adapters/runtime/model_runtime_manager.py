"""Production model lifecycle and session management."""

from __future__ import annotations

import time
from threading import RLock

from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.exceptions import AdapterLoadError
from framework_adapters.integration.ml_engine_bridge import MLEngineAdapterBridge
from framework_adapters.registry.adapter_record import AdapterState
from framework_adapters.runtime.adapter_runtime_context import AdapterRuntimeContext
from framework_adapters.runtime.model_runtime_state import ModelRuntimeState
from framework_adapters.runtime.model_session_record import ModelSessionRecord
from framework_adapters.runtime.model_session_registry import (
    ModelSessionRegistry,
    build_model_session_key,
)
from framework_adapters.runtime.runtime_validator import AdapterRuntimeValidator
from ml_runtime.execution.execution_result import ExecutionResult
from ml_runtime.execution.model_executor import ModelExecutor
from ml_runtime.runtime.ml_runtime import MLRuntime
from ml_runtime.runtime.runtime_context import RuntimeContext
from models.common import utc_now


class ModelRuntimeManager:
    """Adapter-agnostic model session lifecycle manager."""

    def __init__(
        self,
        *,
        ml_runtime: MLRuntime,
        bridge: MLEngineAdapterBridge,
        validator: AdapterRuntimeValidator,
        session_registry: ModelSessionRegistry | None = None,
    ) -> None:
        self._ml_runtime = ml_runtime
        self._bridge = bridge
        self._validator = validator
        self._registry = session_registry or ModelSessionRegistry()
        self._lock = RLock()
        self._warm = False
        self._lazy_initialized = False

    @property
    def session_registry(self) -> ModelSessionRegistry:
        return self._registry

    @property
    def warm(self) -> bool:
        return self._warm

    @property
    def lazy_initialized(self) -> bool:
        return self._lazy_initialized

    def build_session_key(
        self,
        adapter_id: str,
        *,
        context: AdapterRuntimeContext,
    ) -> str:
        artifact_id = str(context.attributes.get("artifact_id", ""))
        return build_model_session_key(
            model_id=context.model_id,
            artifact_id=artifact_id,
            adapter_id=adapter_id,
            model_version=context.model_version,
        )

    def get_or_load_model(
        self,
        adapter_id: str,
        *,
        context: AdapterRuntimeContext,
    ) -> ModelExecutor:
        """Return a cached session or load the model once and cache it."""
        session_key = self.build_session_key(adapter_id, context=context)
        cached = self._registry.lookup(session_key)
        if cached is not None and cached.state == ModelRuntimeState.READY:
            self._registry.increment_ref_count(session_key)
            self._registry.touch(session_key)
            self._bridge.metrics_collector.record_session_reuse()
            self._bridge.metrics_collector.record_cache_hit()
            self._bridge.lifecycle.emit_model_reused(
                adapter_id=adapter_id,
                model_id=context.model_id,
                artifact_id=str(context.attributes.get("artifact_id", "")),
                correlation_id=context.model_id or adapter_id,
                trace_id=context.model_id or adapter_id,
            )
            return self._registry.get_executor(session_key)

        if cached is not None and cached.state == ModelRuntimeState.FAILED:
            self.unload_model(session_key, force=True)

        self._bridge.metrics_collector.record_cache_miss()
        return self.load_model(adapter_id, context=context)

    def load_model(
        self,
        adapter_id: str,
        *,
        context: AdapterRuntimeContext,
    ) -> ModelExecutor:
        """Load a model through the framework adapter and cache the session."""
        session_key = self.build_session_key(adapter_id, context=context)
        load_started = time.monotonic() * 1000.0
        self._bridge.lifecycle.emit_model_loading(
            adapter_id=adapter_id,
            model_id=context.model_id,
            artifact_id=str(context.attributes.get("artifact_id", "")),
            correlation_id=context.model_id or adapter_id,
            trace_id=context.model_id or adapter_id,
        )
        self._upsert_loading_record(session_key, adapter_id=adapter_id, context=context)

        adapter = self._bridge.registry.get_adapter(adapter_id)
        validation = self._validator.validate_model_compatibility(adapter, context=context)
        if not validation.valid:
            message = validation.errors[0] if validation.errors else "model validation failed"
            self._emit_load_failure(adapter_id, session_key, message=message, context=context)
            self._bridge.validator.ensure_valid(validation)

        load_metadata = self._build_load_metadata(context)
        try:
            adapter.load_artifact(
                artifact_reference=context.artifact_reference or adapter_id,
                metadata=load_metadata,
            )
            executor = adapter.create_executor()
            executor_validation = self._validator.validate_executor_ready(executor)
            if not executor_validation.valid:
                message = (
                    executor_validation.errors[0]
                    if executor_validation.errors
                    else "executor validation failed"
                )
                self._emit_load_failure(adapter_id, session_key, message=message, context=context)
                self._bridge.validator.ensure_valid(executor_validation)
        except Exception as error:
            msg = f"model load failed: {error}"
            self._emit_load_failure(adapter_id, session_key, message=msg, context=context)
            raise AdapterLoadError(msg) from error

        record = self._bridge.registry.lookup(adapter_id)
        capability_names = tuple(cap.value for cap in adapter.capabilities())
        self._bridge.register_executor(
            executor,
            name=record.metadata.name,
            version=record.metadata.version,
            capabilities=capability_names,
        )

        load_time_ms = max(0.0, time.monotonic() * 1000.0 - load_started)
        self._bridge.registry.update_state(adapter_id, AdapterState.LOADED)
        self._bridge.lifecycle.emit_adapter_loaded(
            adapter_id=adapter_id,
            name=record.metadata.name,
            version=record.metadata.version,
            correlation_id=context.model_id or adapter_id,
            trace_id=context.model_id or adapter_id,
        )
        self._bridge.metrics_collector.record_load()
        self._bridge.metrics_collector.record_model_load()
        self._bridge.metrics_collector.record_load_time(load_time_ms)
        self._bridge.metrics_collector.record_initialization_latency(load_time_ms)
        self._bridge.metrics_collector.record_state(AdapterState.LOADED)

        session_record = ModelSessionRecord(
            session_id=ModelSessionRegistry.new_session_id(),
            model_id=context.model_id,
            artifact_id=str(context.attributes.get("artifact_id", "")),
            adapter_id=adapter_id,
            framework=context.engine_type.value,
            executor_id=context.executor_id or executor.executor_id(),
            model_version=context.model_version,
            loaded_at=utc_now(),
            last_access_at=utc_now(),
            reference_count=1,
            memory_footprint=self._memory_footprint(adapter, context=context),
            state=ModelRuntimeState.READY,
            warm=self._warm,
            cached=True,
            reload_required=False,
        )
        self._registry.register(
            session_key=session_key,
            record=session_record,
            executor=executor,
        )
        self._bridge.lifecycle.emit_model_ready(
            adapter_id=adapter_id,
            model_id=context.model_id,
            artifact_id=session_record.artifact_id,
            correlation_id=context.model_id or adapter_id,
            trace_id=context.model_id or adapter_id,
        )
        return executor

    def preload_model(
        self,
        adapter_id: str,
        *,
        context: AdapterRuntimeContext,
    ) -> ModelExecutor:
        """Eagerly load a model into the session cache."""
        return self.load_model(adapter_id, context=context)

    def warm_initialize(
        self,
        contexts: tuple[AdapterRuntimeContext, ...] = (),
        *,
        adapter_id: str | None = None,
    ) -> None:
        """Warm-start registered adapters and optionally preload configured models."""
        started = time.monotonic() * 1000.0
        with self._lock:
            self._warm = True
            self._lazy_initialized = True

        target_adapter = adapter_id or self._bridge.registry.get_default_adapter_id()
        if target_adapter is not None:
            adapter = self._bridge.registry.get_adapter(target_adapter)
            adapter.validate_environment()

        for context in contexts:
            resolved_adapter = adapter_id or target_adapter
            if resolved_adapter is None:
                continue
            self.preload_model(resolved_adapter, context=context)

        duration_ms = max(0.0, time.monotonic() * 1000.0 - started)
        self._bridge.metrics_collector.record_warm_start_duration(duration_ms)

    def lazy_initialize(self) -> None:
        """Mark the runtime manager ready without loading models."""
        with self._lock:
            self._lazy_initialized = True

    def unload_model(
        self,
        session_key: str,
        *,
        force: bool = False,
    ) -> None:
        """Unload a cached model session when reference count reaches zero."""
        record = self._registry.lookup(session_key)
        if record is None:
            return
        if not force and record.reference_count > 1:
            self._registry.decrement_ref_count(session_key)
            return

        self._registry.update(session_key, state=ModelRuntimeState.UNLOADING)
        adapter = self._bridge.registry.get_adapter(record.adapter_id)
        adapter.shutdown()
        self._ml_runtime.registry.unregister_executor(record.executor_id)
        self._bridge.registry.update_state(record.adapter_id, AdapterState.REGISTERED)
        self._bridge.lifecycle.emit_model_unloaded(
            adapter_id=record.adapter_id,
            model_id=record.model_id,
            artifact_id=record.artifact_id,
            correlation_id=record.model_id or record.adapter_id,
            trace_id=record.model_id or record.adapter_id,
        )
        self._bridge.metrics_collector.record_model_unload()
        self._registry.update(
            session_key,
            state=ModelRuntimeState.UNLOADED,
            cached=False,
            reference_count=0,
        )
        self._registry.remove(session_key)

    def reload_model(
        self,
        session_key: str,
        *,
        context: AdapterRuntimeContext,
        adapter_id: str | None = None,
    ) -> ModelExecutor:
        """Reload a model session, replacing the cached executor."""
        record = self._registry.lookup(session_key)
        resolved_adapter = adapter_id or (record.adapter_id if record is not None else None)
        if resolved_adapter is None:
            msg = f"model session not found: {session_key}"
            raise AdapterLoadError(msg)

        if record is not None:
            self._registry.update(
                session_key,
                state=ModelRuntimeState.RELOADING,
                reload_required=True,
            )
            self.unload_model(session_key, force=True)

        executor = self.load_model(resolved_adapter, context=context)
        self._bridge.metrics_collector.record_model_reload()
        self._bridge.lifecycle.emit_model_reloaded(
            adapter_id=resolved_adapter,
            model_id=context.model_id,
            artifact_id=str(context.attributes.get("artifact_id", "")),
            correlation_id=context.model_id or resolved_adapter,
            trace_id=context.model_id or resolved_adapter,
        )
        return executor

    def replace_session(
        self,
        session_key: str,
        *,
        executor: ModelExecutor,
        record_updates: dict[str, object] | None = None,
    ) -> ModelSessionRecord:
        """Replace the executor for an existing cached session."""
        updates = {
            "state": ModelRuntimeState.READY,
            "reload_required": False,
            "cached": True,
            "last_access_at": utc_now(),
            **(record_updates or {}),
        }
        return self._registry.replace_executor(
            session_key,
            executor=executor,
            record_updates=updates,
        )

    def invalidate_cache(
        self,
        *,
        session_key: str | None = None,
        model_id: str | None = None,
    ) -> int:
        """Invalidate cached sessions by key or model id."""
        removed = 0
        if session_key is not None:
            record = self._registry.lookup(session_key)
            if record is not None:
                self.unload_model(session_key, force=True)
                removed = 1
            return removed

        if model_id is not None:
            for record in self._registry.list_by_model_id(model_id):
                key = build_model_session_key(
                    model_id=record.model_id,
                    artifact_id=record.artifact_id,
                    adapter_id=record.adapter_id,
                    model_version=record.model_version,
                )
                self.unload_model(key, force=True)
                removed += 1
        return removed

    def shutdown(self) -> None:
        """Gracefully unload all cached model sessions."""
        for record in self._registry.list_records():
            session_key = build_model_session_key(
                model_id=record.model_id,
                artifact_id=record.artifact_id,
                adapter_id=record.adapter_id,
                model_version=record.model_version,
            )
            if record.state not in {ModelRuntimeState.UNLOADED}:
                self.unload_model(session_key, force=True)
        with self._lock:
            self._warm = False
            self._lazy_initialized = False
        self._registry.clear()

    def _upsert_loading_record(
        self,
        session_key: str,
        *,
        adapter_id: str,
        context: AdapterRuntimeContext,
    ) -> None:
        existing = self._registry.lookup(session_key)
        if existing is not None:
            self._registry.update(session_key, state=ModelRuntimeState.LOADING)
            return
        loading_record = ModelSessionRecord(
            session_id=ModelSessionRegistry.new_session_id(),
            model_id=context.model_id,
            artifact_id=str(context.attributes.get("artifact_id", "")),
            adapter_id=adapter_id,
            framework=context.engine_type.value,
            executor_id=context.executor_id or adapter_id,
            model_version=context.model_version,
            state=ModelRuntimeState.LOADING,
            warm=self._warm,
        )
        placeholder = _PlaceholderExecutor(executor_id=loading_record.executor_id)
        self._registry.register(
            session_key=session_key,
            record=loading_record,
            executor=placeholder,
        )

    def _emit_load_failure(
        self,
        adapter_id: str,
        session_key: str,
        *,
        message: str,
        context: AdapterRuntimeContext,
    ) -> None:
        if self._registry.lookup(session_key) is not None:
            self._registry.update(session_key, state=ModelRuntimeState.FAILED)
        self._bridge.lifecycle.emit_model_load_failed(
            adapter_id=adapter_id,
            model_id=context.model_id,
            message=message,
            correlation_id=context.model_id or adapter_id,
            trace_id=context.model_id or adapter_id,
        )
        self._bridge.metrics_collector.record_failure()
        self._bridge.metrics_collector.record_failed_model_load()
        self._bridge.registry.update_state(adapter_id, AdapterState.FAILED)

    @staticmethod
    def _build_load_metadata(context: AdapterRuntimeContext) -> dict[str, object]:
        return {
            "model_id": context.model_id,
            "model_version": context.model_version,
            "artifact_format": context.artifact_format,
            **context.attributes,
        }

    @staticmethod
    def _memory_footprint(
        adapter: FrameworkAdapter,
        *,
        context: AdapterRuntimeContext,
    ) -> dict[str, object]:
        metadata = adapter.metadata()
        return {
            "adapter_id": adapter.adapter_id(),
            "engine_type": metadata.engine_type.value,
            "artifact_format": context.artifact_format,
            "model_version": context.model_version,
        }


class _PlaceholderExecutor(ModelExecutor):
    """Temporary executor placeholder while a model session is loading."""

    def __init__(self, *, executor_id: str) -> None:
        self._executor_id = executor_id

    def executor_id(self) -> str:
        return self._executor_id

    def load(self, *, artifact_reference: str, metadata: dict[str, object]) -> None:
        return None

    def execute(self, context: RuntimeContext) -> ExecutionResult:
        msg = "executor is not ready"
        raise AdapterLoadError(msg)

    def execute_batch(self, contexts: tuple[RuntimeContext, ...]) -> tuple[ExecutionResult, ...]:
        return ()

    def unload(self) -> None:
        return None

    def health(self) -> dict[str, object]:
        return {
            "status": "loading",
            "executor_id": self._executor_id,
            "loaded": False,
            "ready": False,
        }
