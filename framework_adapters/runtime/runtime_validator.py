"""Runtime validation for adapter selection and execution routing."""

from __future__ import annotations

from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.exceptions import AdapterHealthError, AdapterNotFoundError
from framework_adapters.health.adapter_health import FrameworkAdapterHealthChecker
from framework_adapters.health.health_result import HealthStatus
from framework_adapters.registry.adapter_record import AdapterRecord, AdapterState
from framework_adapters.registry.adapter_registry import AdapterRegistry
from framework_adapters.runtime.adapter_runtime_context import AdapterRuntimeContext
from framework_adapters.validation.validation_result import FrameworkAdapterValidationResult
from framework_adapters.validation.validator import FrameworkAdapterValidator
from ml_runtime.exceptions import ExecutorNotFoundError
from ml_runtime.execution.model_executor import ModelExecutor
from ml_runtime.runtime.ml_runtime import MLRuntime


class AdapterRuntimeValidator:
    """Validates adapter runtime operations without framework bindings."""

    def __init__(
        self,
        *,
        registry: AdapterRegistry,
        adapter_validator: FrameworkAdapterValidator | None = None,
        health_checker: FrameworkAdapterHealthChecker | None = None,
    ) -> None:
        self._registry = registry
        self._adapter_validator = adapter_validator or FrameworkAdapterValidator(registry=registry)
        self._health_checker = health_checker or FrameworkAdapterHealthChecker(registry=registry)

    def validate_adapter_exists(self, adapter_id: str) -> FrameworkAdapterValidationResult:
        try:
            self._registry.lookup(adapter_id)
        except AdapterNotFoundError:
            return FrameworkAdapterValidationResult.failure(
                f"adapter not registered: {adapter_id}",
                adapter_id=adapter_id,
            )
        return FrameworkAdapterValidationResult.success(adapter_id=adapter_id)

    def validate_adapter_healthy(self, adapter_id: str) -> FrameworkAdapterValidationResult:
        try:
            result = self._health_checker.check(adapter_id)
        except AdapterHealthError as error:
            return FrameworkAdapterValidationResult.failure(
                str(error),
                adapter_id=adapter_id,
            )
        if result.status == HealthStatus.UNHEALTHY:
            return FrameworkAdapterValidationResult.failure(
                result.message or "adapter is unhealthy",
                adapter_id=adapter_id,
            )
        return FrameworkAdapterValidationResult.success(adapter_id=adapter_id)

    def validate_compatible_artifact(
        self,
        record: AdapterRecord,
        *,
        context: AdapterRuntimeContext,
    ) -> FrameworkAdapterValidationResult:
        if not context.artifact_format.strip():
            return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)
        supported = record.manifest.supported_artifact_formats
        if supported and context.artifact_format not in supported:
            return FrameworkAdapterValidationResult.failure(
                f"artifact format not supported: {context.artifact_format}",
                adapter_id=record.adapter_id,
            )
        return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)

    def validate_runtime_version(
        self,
        record: AdapterRecord,
        *,
        context: AdapterRuntimeContext,
    ) -> FrameworkAdapterValidationResult:
        if not context.runtime_version.strip():
            return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)
        supported = record.manifest.supported_runtime_versions
        if supported and context.runtime_version not in supported:
            return FrameworkAdapterValidationResult.failure(
                f"runtime version not supported: {context.runtime_version}",
                adapter_id=record.adapter_id,
            )
        return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)

    def validate_executor_available(
        self,
        ml_runtime: MLRuntime,
        *,
        executor_id: str,
    ) -> FrameworkAdapterValidationResult:
        if not executor_id.strip():
            return FrameworkAdapterValidationResult.failure("executor_id must not be empty")
        try:
            ml_runtime.registry.lookup(executor_id)
        except ExecutorNotFoundError:
            return FrameworkAdapterValidationResult.failure(
                f"executor not available: {executor_id}",
            )
        return FrameworkAdapterValidationResult.success(adapter_id=executor_id)

    def validate_selection(
        self,
        record: AdapterRecord,
        *,
        context: AdapterRuntimeContext,
    ) -> FrameworkAdapterValidationResult:
        exists_result = self.validate_adapter_exists(record.adapter_id)
        if not exists_result.valid:
            return exists_result
        if record.state == AdapterState.FAILED:
            return FrameworkAdapterValidationResult.failure(
                "adapter is in failed state",
                adapter_id=record.adapter_id,
            )
        if record.metadata.engine_type != context.engine_type:
            return FrameworkAdapterValidationResult.failure(
                "adapter engine type does not match context",
                adapter_id=record.adapter_id,
            )
        for result in (
            self.validate_compatible_artifact(record, context=context),
            self.validate_runtime_version(record, context=context),
            self.validate_adapter_healthy(record.adapter_id),
        ):
            if not result.valid:
                return result
        return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)

    def validate_load(
        self,
        adapter: FrameworkAdapter,
        *,
        context: AdapterRuntimeContext,
    ) -> FrameworkAdapterValidationResult:
        adapter_result = self._adapter_validator.validate_adapter(adapter, check_duplicate=False)
        if not adapter_result.valid:
            return adapter_result
        record = self._registry.lookup(adapter.adapter_id())
        return self.validate_selection(record, context=context)

    def validate_executor_ready(
        self,
        executor: ModelExecutor,
    ) -> FrameworkAdapterValidationResult:
        health = executor.health()
        status = str(health.get("status", "healthy"))
        if status == "loading":
            return FrameworkAdapterValidationResult.failure(
                "executor is not ready",
                adapter_id=str(health.get("adapter_id", health.get("executor_id", ""))),
            )
        if status not in {"healthy", "degraded"}:
            return FrameworkAdapterValidationResult.failure(
                "executor is not ready",
                adapter_id=str(health.get("adapter_id", health.get("executor_id", ""))),
            )
        return FrameworkAdapterValidationResult.success(
            adapter_id=str(health.get("adapter_id", health.get("executor_id", ""))),
        )

    def validate_model_compatibility(
        self,
        adapter: FrameworkAdapter,
        *,
        context: AdapterRuntimeContext,
    ) -> FrameworkAdapterValidationResult:
        adapter_result = self._adapter_validator.validate_adapter(adapter, check_duplicate=False)
        if not adapter_result.valid:
            return adapter_result
        record = self._registry.lookup(adapter.adapter_id())
        for result in (
            self.validate_selection(record, context=context),
            self.validate_schema_version(record, context=context),
            self.validate_model_version(record, context=context),
            self.validate_checksum_confirmation(context),
            self.validate_opset_compatibility(record, context=context),
        ):
            if not result.valid:
                return result
        return FrameworkAdapterValidationResult.success(adapter_id=adapter.adapter_id())

    def validate_schema_version(
        self,
        record: AdapterRecord,
        *,
        context: AdapterRuntimeContext,
    ) -> FrameworkAdapterValidationResult:
        schema_version = str(context.attributes.get("schema_version", "")).strip()
        if not schema_version:
            return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)
        supported = record.manifest.attributes.get("supported_schema_versions")
        if isinstance(supported, (tuple, list)) and schema_version not in supported:
            return FrameworkAdapterValidationResult.failure(
                f"schema version not supported: {schema_version}",
                adapter_id=record.adapter_id,
            )
        return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)

    def validate_model_version(
        self,
        record: AdapterRecord,
        *,
        context: AdapterRuntimeContext,
    ) -> FrameworkAdapterValidationResult:
        if not context.model_version.strip():
            return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)
        supported = record.manifest.attributes.get("supported_model_versions")
        if isinstance(supported, (tuple, list)) and context.model_version not in supported:
            return FrameworkAdapterValidationResult.failure(
                f"model version not supported: {context.model_version}",
                adapter_id=record.adapter_id,
            )
        return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)

    def validate_checksum_confirmation(
        self,
        context: AdapterRuntimeContext,
    ) -> FrameworkAdapterValidationResult:
        checksum = str(context.attributes.get("checksum", "")).strip()
        if not checksum:
            return FrameworkAdapterValidationResult.success()
        if context.attributes.get("checksum_verified") is not True:
            return FrameworkAdapterValidationResult.failure("checksum confirmation required")
        return FrameworkAdapterValidationResult.success()

    def validate_opset_compatibility(
        self,
        record: AdapterRecord,
        *,
        context: AdapterRuntimeContext,
    ) -> FrameworkAdapterValidationResult:
        opset_version = context.attributes.get("opset_version")
        if opset_version is None:
            return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)
        supported = record.manifest.attributes.get("supported_opsets")
        if not isinstance(supported, (tuple, list)):
            return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)
        opset_text = str(opset_version)
        normalized: int | str = int(opset_text) if opset_text.isdigit() else opset_text
        if normalized not in supported:
            return FrameworkAdapterValidationResult.failure(
                f"opset version not supported: {opset_version}",
                adapter_id=record.adapter_id,
            )
        return FrameworkAdapterValidationResult.success(adapter_id=record.adapter_id)
