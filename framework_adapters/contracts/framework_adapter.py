"""Framework adapter contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from framework_adapters.contracts.adapter_capability import AdapterCapability
from framework_adapters.contracts.adapter_manifest import AdapterManifest
from framework_adapters.contracts.adapter_metadata import AdapterMetadata
from framework_adapters.contracts.engine_type import EngineType
from ml_runtime.execution.model_executor import ModelExecutor


class FrameworkAdapter(ABC):
    """Abstract interface between ML engine plugins and future ML frameworks."""

    @abstractmethod
    def adapter_id(self) -> str:
        """Return the adapter identifier."""

    @abstractmethod
    def engine_type(self) -> EngineType:
        """Return the engine type this adapter supports."""

    @abstractmethod
    def metadata(self) -> AdapterMetadata:
        """Return adapter metadata."""

    @abstractmethod
    def manifest(self) -> AdapterManifest:
        """Return adapter manifest."""

    @abstractmethod
    def capabilities(self) -> tuple[AdapterCapability, ...]:
        """Return supported capabilities."""

    @abstractmethod
    def validate_environment(self) -> dict[str, Any]:
        """Validate adapter environment. Contract validation only."""

    @abstractmethod
    def load_artifact(
        self,
        *,
        artifact_reference: str,
        metadata: dict[str, object],
    ) -> dict[str, object]:
        """Load model artifacts without framework binding."""

    @abstractmethod
    def create_executor(self) -> ModelExecutor:
        """Create a metadata-only executor adapter."""

    @abstractmethod
    def shutdown(self) -> None:
        """Release adapter resources."""
