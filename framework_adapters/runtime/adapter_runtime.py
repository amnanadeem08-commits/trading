"""Framework adapter runtime manager for multi-adapter orchestration."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.integration.ml_engine_bridge import MLEngineAdapterBridge
from framework_adapters.registry.adapter_record import AdapterState
from framework_adapters.runtime.adapter_runtime_context import AdapterRuntimeContext
from framework_adapters.runtime.adapter_runtime_session import AdapterRuntimeSession
from framework_adapters.runtime.adapter_selector import AdapterSelector
from framework_adapters.runtime.model_runtime_manager import ModelRuntimeManager
from framework_adapters.runtime.model_session_registry import build_model_session_key
from framework_adapters.runtime.runtime_validator import AdapterRuntimeValidator
from inference_pipeline.responses.inference_response import InferenceResponse
from ml_runtime.execution.execution_result import ExecutionResult
from ml_runtime.execution.model_executor import ModelExecutor
from ml_runtime.runtime.ml_runtime import MLRuntime
from models.common import utc_now


class AdapterRuntime:
    """Manages adapter initialization, selection, loading, and execution routing."""

    def __init__(
        self,
        *,
        ml_runtime: MLRuntime,
        bridge: MLEngineAdapterBridge,
        default_adapter_id: str | None = None,
    ) -> None:
        self._ml_runtime = ml_runtime
        self._bridge = bridge
        self._default_adapter_id = default_adapter_id
        self._selector = AdapterSelector()
        self._validator = AdapterRuntimeValidator(
            registry=bridge.registry,
            adapter_validator=bridge.validator,
            health_checker=bridge.health_checker,
        )
        self._model_runtime_manager = ModelRuntimeManager(
            ml_runtime=ml_runtime,
            bridge=bridge,
            validator=self._validator,
        )
        self._lock = RLock()
        self._sessions: dict[str, AdapterRuntimeSession] = {}
        self._initialized = False

    @property
    def ml_runtime(self) -> MLRuntime:
        return self._ml_runtime

    @property
    def bridge(self) -> MLEngineAdapterBridge:
        return self._bridge

    @property
    def model_runtime_manager(self) -> ModelRuntimeManager:
        return self._model_runtime_manager

    @property
    def initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        """Initialize the adapter runtime and emit lifecycle events."""
        with self._lock:
            if self._initialized:
                return
            self._initialized = True
        if self._default_adapter_id is not None:
            self._bridge.registry.set_default_adapter(self._default_adapter_id)
        self._bridge.lifecycle.emit_adapter_initialized(
            adapter_id=self._default_adapter_id or "adapter-runtime",
            correlation_id="adapter-runtime",
            trace_id="adapter-runtime",
        )

    def select_adapter(self, context: AdapterRuntimeContext) -> str:
        """Select an adapter for the given runtime context."""
        record, latency_ms = self._selector.select(
            self._bridge.registry,
            context=context,
            default_adapter_id=self._bridge.registry.get_default_adapter_id(),
        )
        validation = self._validator.validate_selection(record, context=context)
        if not validation.valid:
            message = validation.errors[0] if validation.errors else "selection validation failed"
            self._emit_selection_failure(record.adapter_id, message=message)
            self._bridge.validator.ensure_valid(validation)

        self._bridge.lifecycle.emit_adapter_selected(
            adapter_id=record.adapter_id,
            engine_type=context.engine_type.value,
            correlation_id=context.model_id or record.adapter_id,
            trace_id=context.model_id or record.adapter_id,
        )
        self._bridge.metrics_collector.record_usage(record.adapter_id)
        self._bridge.metrics_collector.record_selection_latency(latency_ms)
        return record.adapter_id

    def load_adapter(
        self,
        adapter_id: str,
        *,
        context: AdapterRuntimeContext,
    ) -> ModelExecutor:
        """Load or reuse a model session through the runtime manager."""
        executor = self._model_runtime_manager.get_or_load_model(adapter_id, context=context)
        session = AdapterRuntimeSession(
            session_id=str(uuid4()),
            adapter_id=adapter_id,
            engine_type=context.engine_type,
            state=AdapterState.LOADED,
            created_at=utc_now(),
            loaded_at=utc_now(),
        )
        with self._lock:
            self._sessions[adapter_id] = session
        return executor

    def unload_adapter(self, adapter_id: str) -> None:
        """Unload cached model sessions for an adapter."""
        for record in self._model_runtime_manager.session_registry.list_records():
            if record.adapter_id != adapter_id:
                continue
            session_key = build_model_session_key(
                model_id=record.model_id,
                artifact_id=record.artifact_id,
                adapter_id=record.adapter_id,
                model_version=record.model_version,
            )
            self._model_runtime_manager.unload_model(session_key, force=True)

        self._bridge.lifecycle.emit_adapter_unloaded(
            adapter_id=adapter_id,
            correlation_id=adapter_id,
            trace_id=adapter_id,
        )
        with self._lock:
            session = self._sessions.get(adapter_id)
            if session is not None:
                self._sessions[adapter_id] = session.model_copy(
                    update={"state": AdapterState.REGISTERED, "unloaded_at": utc_now()}
                )

    def route_execution(
        self,
        inference_response: InferenceResponse,
        *,
        context: AdapterRuntimeContext,
    ) -> ExecutionResult:
        """Route execution through adapter selection and ML runtime delegation."""
        adapter_id = self.select_adapter(context)
        executor = self.load_adapter(adapter_id, context=context)
        executor_id = context.executor_id or executor.executor_id()
        executor_validation = self._validator.validate_executor_available(
            self._ml_runtime,
            executor_id=executor_id,
        )
        if not executor_validation.valid:
            message = (
                executor_validation.errors[0]
                if executor_validation.errors
                else "executor validation failed"
            )
            self._emit_load_failure(adapter_id, message=message)
            self._bridge.validator.ensure_valid(executor_validation)

        self._bridge.metrics_collector.record_execution()
        return self._ml_runtime.execute(inference_response, executor_id=executor_id)

    def register_adapter(
        self,
        adapter: FrameworkAdapter,
        *,
        priority: int = 0,
        set_default: bool = False,
    ) -> str:
        """Register an adapter with optional priority and default selection."""
        validation = self._bridge.validator.validate_adapter(adapter)
        if not validation.valid:
            self._bridge.metrics_collector.record_failure()
            self._bridge.validator.ensure_valid(validation)
        record = self._bridge.registry.register(adapter, priority=priority)
        self._bridge.lifecycle.emit_adapter_registered(
            adapter_id=record.adapter_id,
            name=record.metadata.name,
            version=record.metadata.version,
            correlation_id=record.adapter_id,
            trace_id=record.adapter_id,
        )
        self._bridge.metrics_collector.record_state(AdapterState.REGISTERED)
        if set_default:
            self._bridge.registry.set_default_adapter(record.adapter_id)
        return record.adapter_id

    def shutdown(self) -> None:
        """Shut down all adapters and the adapter runtime."""
        self._model_runtime_manager.shutdown()
        for record in self._bridge.registry.list():
            if record.state not in {AdapterState.SHUTDOWN}:
                self._bridge.shutdown_adapter(record.adapter_id)
        with self._lock:
            self._sessions.clear()
            self._initialized = False

    def _emit_selection_failure(self, adapter_id: str, *, message: str) -> None:
        self._bridge.lifecycle.emit_adapter_failed(
            adapter_id=adapter_id,
            message=message,
            correlation_id=adapter_id,
            trace_id=adapter_id,
        )
        self._bridge.metrics_collector.record_failure()

    def _emit_load_failure(self, adapter_id: str, *, message: str) -> None:
        self._bridge.lifecycle.emit_adapter_failed(
            adapter_id=adapter_id,
            message=message,
            correlation_id=adapter_id,
            trace_id=adapter_id,
        )
        self._bridge.metrics_collector.record_failure()
        self._bridge.registry.update_state(adapter_id, AdapterState.FAILED)


def build_adapter_runtime(
    ml_runtime: MLRuntime,
    bridge: MLEngineAdapterBridge,
    *,
    default_adapter_id: str | None = None,
    auto_initialize: bool = True,
    warm_start: bool = False,
    preload_default_models: bool = False,
) -> AdapterRuntime:
    """Create and optionally initialize an adapter runtime."""
    runtime = AdapterRuntime(
        ml_runtime=ml_runtime,
        bridge=bridge,
        default_adapter_id=default_adapter_id,
    )
    if auto_initialize:
        runtime.initialize()
    if warm_start:
        if preload_default_models and default_adapter_id is not None:
            runtime.model_runtime_manager.warm_initialize(adapter_id=default_adapter_id)
        else:
            runtime.model_runtime_manager.warm_initialize()
    return runtime
