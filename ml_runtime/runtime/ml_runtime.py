"""ML runtime facade."""

from __future__ import annotations

import time
from uuid import uuid4

from config.hash import compute_configuration_hash
from events.event_bus import EventBus
from inference_pipeline.responses.inference_response import InferenceResponse
from metrics.registry import MetricRegistry
from ml_runtime.execution.execution_metadata import ExecutionMetadata
from ml_runtime.execution.execution_result import ExecutionResult, ExecutionStatus
from ml_runtime.lifecycle.runtime_lifecycle import RuntimeLifecycleManager
from ml_runtime.metrics.runtime_metrics import RuntimeMetricsCollector
from ml_runtime.metrics.runtime_summary import RuntimeSummary
from ml_runtime.registry.runtime_registry import RuntimeRegistry
from ml_runtime.runtime.runtime_session import RuntimeSessionManager
from ml_runtime.validation.validator import RuntimeValidator
from ml_runtime.versioning.runtime_version import RuntimeVersionRegistry
from models.common import utc_now


class MLRuntime:
    """Framework-agnostic ML runtime orchestration facade."""

    def __init__(
        self,
        *,
        event_bus: EventBus | None = None,
        metrics: MetricRegistry | None = None,
        max_sessions: int = 100,
    ) -> None:
        self.registry = RuntimeRegistry()
        self.session_manager = RuntimeSessionManager(max_sessions=max_sessions)
        self.version_registry = RuntimeVersionRegistry()
        self.metrics_collector = RuntimeMetricsCollector()
        self.validator = RuntimeValidator()
        self._event_bus = event_bus or EventBus()
        self._metric_registry = metrics or MetricRegistry()
        self.lifecycle = RuntimeLifecycleManager(
            event_bus=self._event_bus,
            metrics=self._metric_registry,
        )
        version = self.version_registry.register(
            version_id="ml-runtime-v1",
            runtime_schema="1.0.0",
            configuration_hash=compute_configuration_hash(),
        )
        self.validator.mark_initialized()
        self.lifecycle.emit_runtime_initialized(
            runtime_version=version.runtime_schema,
            correlation_id=str(uuid4()),
            trace_id=str(uuid4()),
        )

    def register_executor(
        self,
        executor: object,
        *,
        name: str,
        version: str,
        capabilities: tuple[str, ...] = (),
    ) -> None:
        from ml_runtime.execution.model_executor import ModelExecutor

        if not isinstance(executor, ModelExecutor):
            msg = "executor must implement ModelExecutor"
            raise TypeError(msg)
        metadata = self.registry.register_executor(
            executor,
            name=name,
            version=version,
            capabilities=capabilities,
        )
        self.lifecycle.emit_executor_registered(
            executor_id=metadata.executor_id,
            name=metadata.name,
            version=metadata.version,
            correlation_id=str(uuid4()),
            trace_id=str(uuid4()),
        )

    def execute(
        self,
        inference_response: InferenceResponse,
        *,
        executor_id: str,
    ) -> ExecutionResult:
        started = time.monotonic() * 1000.0
        metadata = inference_response.metadata
        init_validation = self.validator.validate_initialized()
        self.validator.ensure_valid(init_validation)

        executor_validation = self.validator.validate_executor_exists(executor_id, self.registry)
        self.validator.ensure_valid(executor_validation)

        model_validation = self.validator.validate_model_resolved(metadata)
        self.validator.ensure_valid(model_validation)

        artifact_validation = self.validator.validate_artifact_reference(metadata.artifact_id)
        self.validator.ensure_valid(artifact_validation)

        session = self.session_manager.create(
            request_id=metadata.request_id,
            model_id=metadata.model_id,
            executor_id=executor_id,
        )
        context = self.session_manager.build_context(
            session,
            input_metadata={
                "request_id": metadata.request_id,
                **metadata.attributes,
            },
            model_version=metadata.version_id,
            artifact_reference=metadata.artifact_id,
            config_hash=metadata.config_hash,
            checksum=metadata.checksum,
            correlation_id=metadata.correlation_id,
            trace_id=metadata.trace_id,
        )
        request_validation = self.validator.validate_request_metadata(context)
        self.validator.ensure_valid(request_validation)

        execution_id = f"execution-{uuid4()}"
        self.lifecycle.emit_runtime_started(
            execution_id=execution_id,
            request_id=metadata.request_id,
            model_id=metadata.model_id,
            executor_id=executor_id,
            correlation_id=metadata.correlation_id,
            trace_id=metadata.trace_id,
        )
        self.metrics_collector.record_status(ExecutionStatus.RUNNING)

        executor = self.registry.lookup(executor_id)
        load_started = time.monotonic() * 1000.0
        try:
            executor.load(
                artifact_reference=metadata.artifact_id,
                metadata={"model_id": metadata.model_id, "version_id": metadata.version_id},
            )
            load_time_ms = max(0.0, time.monotonic() * 1000.0 - load_started)
            self.lifecycle.emit_executor_loaded(
                executor_id=executor_id,
                artifact_reference=metadata.artifact_id,
                correlation_id=metadata.correlation_id,
                trace_id=metadata.trace_id,
            )
            self.metrics_collector.record_status(ExecutionStatus.LOADING)

            exec_started = time.monotonic() * 1000.0
            result = executor.execute(context)
            execution_time_ms = max(0.0, time.monotonic() * 1000.0 - exec_started)

            unload_started = time.monotonic() * 1000.0
            executor.unload()
            unload_time_ms = max(0.0, time.monotonic() * 1000.0 - unload_started)
            self.lifecycle.emit_executor_unloaded(
                executor_id=executor_id,
                correlation_id=metadata.correlation_id,
                trace_id=metadata.trace_id,
            )
            self.metrics_collector.record_status(ExecutionStatus.UNLOADED)
        except Exception as error:
            duration_ms = max(0.0, time.monotonic() * 1000.0 - started)
            self.lifecycle.emit_runtime_failed(
                execution_id=execution_id,
                request_id=metadata.request_id,
                model_id=metadata.model_id,
                message=str(error),
                correlation_id=metadata.correlation_id,
                trace_id=metadata.trace_id,
            )
            self.metrics_collector.record_status(ExecutionStatus.FAILED)
            self.metrics_collector.record_timing(runtime_latency_ms=duration_ms)
            self.session_manager.update(session.session_id, status=ExecutionStatus.FAILED)
            return ExecutionResult(
                execution_id=execution_id,
                request_id=metadata.request_id,
                status=ExecutionStatus.FAILED,
                message=str(error),
            )

        completed_at = utc_now()
        duration_ms = max(0.0, time.monotonic() * 1000.0 - started)
        executor_attributes: dict[str, object] = {}
        if result.metadata is not None:
            executor_attributes = dict(result.metadata.attributes)
        execution_metadata = ExecutionMetadata(
            execution_id=execution_id,
            request_id=metadata.request_id,
            model_id=metadata.model_id,
            model_version=metadata.version_id,
            artifact_reference=metadata.artifact_id,
            executor_id=executor_id,
            correlation_id=metadata.correlation_id,
            trace_id=metadata.trace_id,
            started_at=metadata.started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            load_time_ms=load_time_ms,
            attributes={
                **executor_attributes,
                "config_hash": metadata.config_hash,
            },
        )
        final_result = ExecutionResult(
            execution_id=execution_id,
            request_id=metadata.request_id,
            status=ExecutionStatus.COMPLETED,
            metadata=execution_metadata,
            message=result.message or "runtime execution completed",
        )
        self.session_manager.update(
            session.session_id,
            status=ExecutionStatus.COMPLETED,
            result=final_result,
        )
        self.lifecycle.emit_runtime_completed(
            execution_id=execution_id,
            request_id=metadata.request_id,
            model_id=metadata.model_id,
            executor_id=executor_id,
            correlation_id=metadata.correlation_id,
            trace_id=metadata.trace_id,
        )
        self.metrics_collector.record_status(ExecutionStatus.COMPLETED)
        self.metrics_collector.record_timing(
            runtime_latency_ms=duration_ms,
            load_time_ms=load_time_ms,
            execution_time_ms=execution_time_ms,
            unload_time_ms=unload_time_ms,
        )
        self.metrics_collector.record_summary(
            RuntimeSummary(
                execution_id=execution_id,
                request_id=metadata.request_id,
                model_id=metadata.model_id,
                executor_id=executor_id,
                status=ExecutionStatus.COMPLETED,
                runtime_latency_ms=duration_ms,
                load_time_ms=load_time_ms,
                execution_time_ms=execution_time_ms,
                unload_time_ms=unload_time_ms,
            )
        )
        return final_result

    def shutdown(self) -> None:
        self.lifecycle.emit_runtime_shutdown(
            correlation_id=str(uuid4()),
            trace_id=str(uuid4()),
        )
        self.session_manager.clear()
        self.registry.clear()


def build_ml_runtime(*, max_sessions: int = 100) -> MLRuntime:
    """Create a configured ML runtime instance."""
    return MLRuntime(max_sessions=max_sessions)
