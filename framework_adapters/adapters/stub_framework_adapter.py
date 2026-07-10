"""Concrete stub framework adapter implementation."""

from __future__ import annotations

from typing import Any

from framework_adapters.adapters.stub_environment import StubEnvironment
from framework_adapters.adapters.stub_executor_factory import StubExecutorFactory
from framework_adapters.contracts.adapter_capability import AdapterCapability
from framework_adapters.contracts.adapter_manifest import AdapterManifest
from framework_adapters.contracts.adapter_metadata import AdapterMetadata
from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from ml_engine_plugins.engines.stub_executor import STUB_ENGINE_ID
from ml_runtime.execution.model_executor import ModelExecutor
from models.common import utc_now

STUB_ADAPTER_ID = "stub-framework-adapter"
STUB_ADAPTER_VERSION = "1.0.0"
STUB_ADAPTER_NAME = "Stub Framework Adapter"

__all__ = [
    "STUB_ADAPTER_ID",
    "STUB_ADAPTER_NAME",
    "STUB_ADAPTER_VERSION",
    "StubFrameworkAdapter",
    "create_stub_adapter",
]


class StubFrameworkAdapter(FrameworkAdapter):
    """Concrete stub adapter proving the framework adapter registration path."""

    def __init__(
        self,
        *,
        adapter_id: str = STUB_ADAPTER_ID,
        name: str = STUB_ADAPTER_NAME,
        version: str = STUB_ADAPTER_VERSION,
        executor_id: str = STUB_ENGINE_ID,
        environment: StubEnvironment | None = None,
        executor_factory: StubExecutorFactory | None = None,
    ) -> None:
        self._adapter_id = adapter_id
        self._name = name
        self._version = version
        self._executor_id = executor_id
        self._environment = environment or StubEnvironment()
        self._executor_factory = executor_factory or StubExecutorFactory()
        self._artifact_loaded = False

    def adapter_id(self) -> str:
        return self._adapter_id

    def engine_type(self) -> EngineType:
        return EngineType.STUB

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_id=self._adapter_id,
            name=self._name,
            version=self._version,
            author="platform",
            description="Concrete stub framework adapter for architecture validation",
            engine_type=EngineType.STUB,
            registered_at=utc_now(),
        )

    def manifest(self) -> AdapterManifest:
        return AdapterManifest(
            adapter_id=self._adapter_id,
            name=self._name,
            version=self._version,
            author="platform",
            description="Concrete stub framework adapter for architecture validation",
            engine_type=EngineType.STUB,
            framework_requirements=(),
            supported_artifact_formats=("stub",),
            supported_runtime_versions=("1.0.0",),
            capabilities=(
                AdapterCapability.LOAD_ARTIFACT,
                AdapterCapability.BATCH_EXECUTION,
                AdapterCapability.ONLINE_EXECUTION,
                AdapterCapability.CPU_SUPPORTED,
            ),
            entrypoint="framework_adapters.adapters.stub_framework_adapter",
            attributes={"sandbox": True},
        )

    def capabilities(self) -> tuple[AdapterCapability, ...]:
        return self.manifest().capabilities

    def validate_environment(self) -> dict[str, Any]:
        result = self._environment.check_environment()
        return {
            **result,
            "adapter_id": self._adapter_id,
            "engine_type": EngineType.STUB.value,
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

    @property
    def artifact_loaded(self) -> bool:
        return self._artifact_loaded


def create_stub_adapter() -> StubFrameworkAdapter:
    """Create the default stub framework adapter."""
    return StubFrameworkAdapter()
