"""ML model registry."""

from __future__ import annotations

from threading import RLock

from ml.exceptions import ModelNotFoundError, ModelRegistrationError
from ml.models.model import MLModel
from ml.models.model_metadata import ModelMetadata

_default_model_registry: ModelRegistry | None = None
_registry_lock = RLock()


class ModelRegistry:
    """Thread-safe registry for ML model definitions and implementations."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._metadata: dict[str, ModelMetadata] = {}
        self._types: dict[str, type[MLModel]] = {}

    def register_metadata(self, metadata: ModelMetadata) -> None:
        """Register model metadata."""
        model_id = metadata.model_id
        if not model_id.strip():
            msg = "Model id must not be empty"
            raise ModelRegistrationError(msg)
        with self._lock:
            if model_id in self._metadata:
                msg = f"Model already registered: {model_id}"
                raise ModelRegistrationError(msg)
            self._metadata[model_id] = metadata

    def register_type(self, model_type: type[MLModel]) -> None:
        """Register an ML model implementation type."""
        instance = model_type()
        model_id = instance.model_id()
        with self._lock:
            self._types[model_id] = model_type
            if model_id not in self._metadata:
                self._metadata[model_id] = instance.metadata()

    def unregister(self, model_id: str) -> None:
        with self._lock:
            if model_id not in self._metadata:
                raise ModelNotFoundError(model_id)
            del self._metadata[model_id]
            self._types.pop(model_id, None)

    def resolve_metadata(self, model_id: str) -> ModelMetadata:
        with self._lock:
            metadata = self._metadata.get(model_id)
        if metadata is None:
            raise ModelNotFoundError(model_id)
        return metadata

    def resolve_type(self, model_id: str) -> type[MLModel]:
        with self._lock:
            model_type = self._types.get(model_id)
        if model_type is None:
            raise ModelNotFoundError(model_id)
        return model_type

    def exists(self, model_id: str) -> bool:
        with self._lock:
            return model_id in self._metadata

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._metadata.keys()))

    def list_types(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._types.keys()))


def get_model_definition_registry() -> ModelRegistry:
    """Return the process-wide default model registry."""
    global _default_model_registry
    with _registry_lock:
        if _default_model_registry is None:
            _default_model_registry = ModelRegistry()
        return _default_model_registry


def reset_model_definition_registry() -> None:
    """Reset the default model registry. Intended for tests."""
    global _default_model_registry
    with _registry_lock:
        _default_model_registry = None
