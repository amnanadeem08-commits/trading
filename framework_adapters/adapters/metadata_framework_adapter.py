"""Metadata-only configurable framework adapter for runtime testing."""

from __future__ import annotations

from typing import Any

from framework_adapters.adapters.stub_environment import StubEnvironment
from framework_adapters.adapters.stub_executor_factory import StubExecutorFactory
from framework_adapters.contracts.adapter_capability import AdapterCapability
from framework_adapters.contracts.adapter_manifest import AdapterManifest
from framework_adapters.contracts.adapter_metadata import AdapterMetadata
from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from ml_runtime.execution.model_executor import ModelExecutor
from models.common import utc_now


class MetadataFrameworkAdapter(FrameworkAdapter):
    """Configurable metadata-only adapter for multi-engine runtime selection."""

    def __init__(
        self,
        *,
        adapter_id: str,
        name: str,
        version: str,
        engine_type: EngineType,
        supported_artifact_formats: tuple[str, ...] = ("stub",),
        supported_runtime_versions: tuple[str, ...] = ("1.0.0",),
        priority: int = 0,
        executor_id: str | None = None,
        environment: StubEnvironment | None = None,
        executor_factory: StubExecutorFactory | None = None,
    ) -> None:
        self._adapter_id = adapter_id
        self._name = name
        self._version = version
        self._engine_type = engine_type
        self._supported_artifact_formats = supported_artifact_formats
        self._supported_runtime_versions = supported_runtime_versions
        self._priority = priority
        self._executor_id = executor_id or adapter_id
        self._environment = environment or StubEnvironment()
        self._executor_factory = executor_factory or StubExecutorFactory()
        self._artifact_loaded = False

    def adapter_id(self) -> str:
        return self._adapter_id

    def engine_type(self) -> EngineType:
        return self._engine_type

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_id=self._adapter_id,
            name=self._name,
            version=self._version,
            author="platform",
            description="Metadata-only framework adapter for runtime selection",
            engine_type=self._engine_type,
            registered_at=utc_now(),
            attributes={"priority": self._priority},
        )

    def manifest(self) -> AdapterManifest:
        return AdapterManifest(
            adapter_id=self._adapter_id,
            name=self._name,
            version=self._version,
            author="platform",
            description="Metadata-only framework adapter for runtime selection",
            engine_type=self._engine_type,
            framework_requirements=(),
            supported_artifact_formats=self._supported_artifact_formats,
            supported_runtime_versions=self._supported_runtime_versions,
            capabilities=(
                AdapterCapability.LOAD_ARTIFACT,
                AdapterCapability.BATCH_EXECUTION,
                AdapterCapability.CPU_SUPPORTED,
            ),
            entrypoint="framework_adapters.adapters.metadata_framework_adapter",
            attributes={"priority": self._priority, "sandbox": True},
        )

    def capabilities(self) -> tuple[AdapterCapability, ...]:
        return self.manifest().capabilities

    def validate_environment(self) -> dict[str, Any]:
        result = self._environment.check_environment()
        return {
            **result,
            "adapter_id": self._adapter_id,
            "engine_type": self._engine_type.value,
            "sandbox": True,
        }

    def load_artifact(
        self,
        *,
        artifact_reference: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        self._artifact_loaded = True
        return {
            "adapter_id": self._adapter_id,
            "artifact_reference": artifact_reference,
            "loaded": True,
            "metadata": metadata,
        }

    def create_executor(self) -> ModelExecutor:
        return self._executor_factory.create(executor_id=self._executor_id)

    def shutdown(self) -> None:
        self._artifact_loaded = False
