"""Model loader for production model resolution."""

from __future__ import annotations

from inference_pipeline.exceptions import ModelResolutionError
from model_registry.exceptions import ModelNotFoundError
from model_registry.models.model_stage import ModelStage
from model_registry.models.model_version import ModelVersion
from model_registry.models.registered_model import RegisteredModel
from model_registry.registry.model_registry import ModelRegistryStore


class ModelLoader:
    """Resolves production models and artifact references without ML execution."""

    def __init__(self, registry: ModelRegistryStore) -> None:
        self._registry = registry

    def resolve_model(self, model_id: str) -> RegisteredModel:
        try:
            return self._registry.lookup(model_id)
        except ModelNotFoundError as error:
            raise ModelResolutionError(str(error)) from error

    def resolve_production_version(self, model_id: str) -> ModelVersion:
        try:
            versions = self._registry.versions(model_id)
        except ModelNotFoundError as error:
            raise ModelResolutionError(str(error)) from error
        production = tuple(v for v in versions if v.stage == ModelStage.PRODUCTION)
        if production:
            return production[-1]
        msg = f"No production version found for model {model_id}"
        raise ModelResolutionError(msg)

    def resolve_version(self, model_id: str, *, version_id: str | None = None) -> ModelVersion:
        if version_id is not None:
            version = self._registry.get_version(version_id)
            if version.model_id != model_id:
                msg = f"Version {version_id} does not belong to model {model_id}"
                raise ModelResolutionError(msg)
            return version
        return self.resolve_production_version(model_id)

    def validate_production_stage(self, version: ModelVersion) -> None:
        if version.stage != ModelStage.PRODUCTION:
            msg = f"Model version {version.version_id} is not in production stage"
            raise ModelResolutionError(msg)

    def load_artifact_reference(self, version: ModelVersion) -> str:
        if not version.artifact_id.strip():
            msg = f"Artifact reference missing for version {version.version_id}"
            raise ModelResolutionError(msg)
        return version.artifact_id
