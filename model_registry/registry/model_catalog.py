"""Model catalog for registry discovery."""

from __future__ import annotations

from threading import RLock

from model_registry.models.model_metadata import ModelMetadata
from model_registry.models.model_version import ModelVersion
from model_registry.models.registered_model import RegisteredModel
from models.common import PlatformModel


class ModelCatalogEntry(PlatformModel):
    """Catalog entry combining model and version metadata."""

    model: RegisteredModel
    versions: tuple[ModelVersion, ...]


class ModelCatalog:
    """Lists models, versions, and metadata from the registry."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, ModelCatalogEntry] = {}

    def upsert(self, model: RegisteredModel, versions: tuple[ModelVersion, ...]) -> None:
        with self._lock:
            self._entries[model.model_id] = ModelCatalogEntry(model=model, versions=versions)

    def get(self, model_id: str) -> ModelCatalogEntry | None:
        with self._lock:
            return self._entries.get(model_id)

    def list_models(self) -> tuple[RegisteredModel, ...]:
        with self._lock:
            return tuple(entry.model for entry in self._entries.values())

    def list_metadata(self) -> tuple[ModelMetadata, ...]:
        with self._lock:
            return tuple(entry.model.metadata for entry in self._entries.values())

    def list_versions(self, model_id: str) -> tuple[ModelVersion, ...]:
        with self._lock:
            entry = self._entries.get(model_id)
            if entry is None:
                return ()
            return entry.versions

    def list_all_versions(self) -> tuple[ModelVersion, ...]:
        with self._lock:
            versions: list[ModelVersion] = []
            for entry in self._entries.values():
                versions.extend(entry.versions)
            return tuple(versions)
