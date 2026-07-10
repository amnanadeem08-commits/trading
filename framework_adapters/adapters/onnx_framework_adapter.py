"""Concrete inference-runtime framework adapter."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from framework_adapters.adapters.ort_executor import (
    OrtModelExecutor,
    _import_ort,
    _ort_engine_value,
)
from framework_adapters.adapters.ort_path_resolver import resolve_model_path
from framework_adapters.contracts.adapter_capability import AdapterCapability
from framework_adapters.contracts.adapter_manifest import AdapterManifest
from framework_adapters.contracts.adapter_metadata import AdapterMetadata
from framework_adapters.contracts.engine_type import EngineType
from framework_adapters.contracts.framework_adapter import FrameworkAdapter
from framework_adapters.exceptions import AdapterLoadError
from ml_runtime.execution.model_executor import ModelExecutor
from models.common import utc_now

ORT_ADAPTER_ID = "ort-framework-adapter"
ORT_ADAPTER_VERSION = "1.0.0"
ORT_ADAPTER_NAME = "ORT Framework Adapter"
_ORT_FORMAT = "ort"
_ORT_MODULE = "onnxruntime"


def _ort_engine_type() -> EngineType:
    target = _ort_engine_value()
    for candidate in EngineType:
        if candidate.value == target:
            return candidate
    msg = "ORT engine type is not configured"
    raise AdapterLoadError(msg)


class OrtFrameworkAdapter(FrameworkAdapter):
    """Loads serialized inference models and creates runtime executors."""

    def __init__(
        self,
        *,
        adapter_id: str = ORT_ADAPTER_ID,
        name: str = ORT_ADAPTER_NAME,
        version: str = ORT_ADAPTER_VERSION,
        executor_id: str = ORT_ADAPTER_ID,
        priority: int = 200,
    ) -> None:
        self._adapter_id = adapter_id
        self._name = name
        self._version = version
        self._executor_id = executor_id
        self._priority = priority
        self._model_path: Path | None = None
        self._artifact_loaded = False
        self._runtime_version = ""
        self._initialization_time_ms = 0.0

    def adapter_id(self) -> str:
        return self._adapter_id

    def engine_type(self) -> EngineType:
        return _ort_engine_type()

    def metadata(self) -> AdapterMetadata:
        return AdapterMetadata(
            adapter_id=self._adapter_id,
            name=self._name,
            version=self._version,
            author="platform",
            description="Concrete inference-runtime framework adapter",
            engine_type=_ort_engine_type(),
            registered_at=utc_now(),
            attributes={
                "priority": self._priority,
                "runtime_version": self._runtime_version,
            },
        )

    def manifest(self) -> AdapterManifest:
        return AdapterManifest(
            adapter_id=self._adapter_id,
            name=self._name,
            version=self._version,
            author="platform",
            description="Concrete inference-runtime framework adapter",
            engine_type=_ort_engine_type(),
            framework_requirements=(_ORT_MODULE,),
            supported_artifact_formats=(_ORT_FORMAT, "bin"),
            supported_runtime_versions=(ORT_ADAPTER_VERSION,),
            capabilities=(
                AdapterCapability.LOAD_ARTIFACT,
                AdapterCapability.BATCH_EXECUTION,
                AdapterCapability.ONLINE_EXECUTION,
                AdapterCapability.CPU_SUPPORTED,
            ),
            entrypoint="framework_adapters.adapters.onnx_framework_adapter",
            attributes={"priority": self._priority, "sandbox": False, "supported_opsets": (17,)},
        )

    def capabilities(self) -> tuple[AdapterCapability, ...]:
        return self.manifest().capabilities

    def validate_environment(self) -> dict[str, Any]:
        started = time.monotonic() * 1000.0
        try:
            ort = _import_ort()
            self._runtime_version = str(getattr(ort, "__version__", "unknown"))
            self._initialization_time_ms = max(0.0, time.monotonic() * 1000.0 - started)
            return {
                "status": "healthy",
                "adapter_id": self._adapter_id,
                "engine_type": _ort_engine_value(),
                "runtime_version": self._runtime_version,
                "framework_available": True,
                "initialization_time_ms": self._initialization_time_ms,
            }
        except Exception as error:
            return {
                "status": "unhealthy",
                "adapter_id": self._adapter_id,
                "engine_type": _ort_engine_value(),
                "framework_available": False,
                "message": str(error),
            }

    def load_artifact(
        self,
        *,
        artifact_reference: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        model_path = resolve_model_path(
            artifact_reference=artifact_reference,
            metadata=metadata,
            fallback_path=self._model_path,
        )
        ort = _import_ort()
        try:
            session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        except Exception as error:
            msg = f"artifact load failed: {error}"
            raise AdapterLoadError(msg) from error
        session.get_inputs()
        self._model_path = model_path
        self._artifact_loaded = True
        return {
            "adapter_id": self._adapter_id,
            "artifact_reference": artifact_reference,
            "loaded": True,
            "path": str(model_path),
            "runtime_version": self._runtime_version,
            "metadata": metadata,
        }

    def create_executor(self) -> ModelExecutor:
        if not self._artifact_loaded or self._model_path is None:
            msg = "artifact must be loaded before creating executor"
            raise AdapterLoadError(msg)
        return OrtModelExecutor(
            executor_id=self._executor_id,
            adapter_id=self._adapter_id,
            model_path=self._model_path,
        )

    def shutdown(self) -> None:
        self._artifact_loaded = False
        self._model_path = None

    @property
    def artifact_loaded(self) -> bool:
        return self._artifact_loaded


def create_ort_adapter() -> OrtFrameworkAdapter:
    """Create the default ORT framework adapter."""
    return OrtFrameworkAdapter()
