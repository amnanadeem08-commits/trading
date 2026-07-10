"""Model registry core."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from model_registry.exceptions import (
    ModelNotFoundError,
    ModelRegistrationError,
    ModelVersionNotFoundError,
)
from model_registry.models.model_stage import ModelStage
from model_registry.models.model_status import ModelStatus
from model_registry.models.model_version import ModelVersion
from model_registry.models.registered_model import RegisteredModel
from model_registry.registry.model_catalog import ModelCatalog
from model_registry.registry.promotion_registry import PromotionRegistry
from model_registry.validation.validator import RegistryValidator
from models.common import utc_now


class ModelRegistryStore:
    """Thread-safe in-memory model registry."""

    def __init__(
        self,
        *,
        catalog: ModelCatalog | None = None,
        promotion_registry: PromotionRegistry | None = None,
        validator: RegistryValidator | None = None,
        max_registered_models: int = 100,
        max_versions_per_model: int = 50,
        approval_required: bool = True,
        immutable_versions: bool = True,
    ) -> None:
        self._lock = RLock()
        self._models: dict[str, RegisteredModel] = {}
        self._versions: dict[str, ModelVersion] = {}
        self._versions_by_model: dict[str, tuple[str, ...]] = {}
        self._catalog = catalog or ModelCatalog()
        self._promotions = promotion_registry or PromotionRegistry()
        self._validator = validator or RegistryValidator()
        self._max_models = max_registered_models
        self._max_versions = max_versions_per_model
        self._approval_required = approval_required
        self._immutable_versions = immutable_versions

    @property
    def catalog(self) -> ModelCatalog:
        return self._catalog

    @property
    def promotion_registry(self) -> PromotionRegistry:
        return self._promotions

    @property
    def validator(self) -> RegistryValidator:
        return self._validator

    def register_model(self, model: RegisteredModel) -> RegisteredModel:
        validation = self._validator.validate_model(model)
        self._validator.ensure_valid(validation)
        with self._lock:
            if len(self._models) >= self._max_models and model.model_id not in self._models:
                msg = f"Maximum registered models ({self._max_models}) reached"
                raise ModelRegistrationError(msg)
            self._models[model.model_id] = model
            self._versions_by_model.setdefault(model.model_id, ())
            self._sync_catalog(model.model_id)
        return model

    def register_version(self, version: ModelVersion) -> ModelVersion:
        with self._lock:
            if version.model_id not in self._models:
                raise ModelNotFoundError(version.model_id)
            existing = tuple(
                self._versions[vid]
                for vid in self._versions_by_model.get(version.model_id, ())
                if vid in self._versions
            )
        validation = self._validator.validate_version(version, existing_versions=existing)
        self._validator.ensure_valid(validation)
        with self._lock:
            model_versions = self._versions_by_model.get(version.model_id, ())
            if len(model_versions) >= self._max_versions:
                msg = f"Maximum versions per model ({self._max_versions}) reached"
                raise ModelRegistrationError(msg)
            stored = version.model_copy(update={"immutable": self._immutable_versions})
            self._versions[version.version_id] = stored
            if version.version_id not in model_versions:
                self._versions_by_model[version.model_id] = (*model_versions, version.version_id)
            model = self._models[version.model_id]
            updated = model.model_copy(update={"latest_version_id": version.version_id})
            self._models[version.model_id] = updated
            self._sync_catalog(version.model_id)
        return stored

    def promote(
        self,
        *,
        version_id: str,
        to_stage: ModelStage,
        approved: bool = True,
    ) -> ModelVersion:
        version = self._get_version(version_id)
        validation = self._validator.validate_promotion(
            version=version,
            to_stage=to_stage,
            approval_required=self._approval_required,
        )
        self._validator.ensure_valid(validation)
        if (
            self._approval_required
            and to_stage in {ModelStage.APPROVED, ModelStage.PRODUCTION}
            and not approved
        ):
            msg = "promotion requires approval"
            from model_registry.exceptions import PromotionError

            raise PromotionError(msg)
        from_stage = version.stage
        promoted = version.model_copy(update={"stage": to_stage})
        with self._lock:
            self._versions[version_id] = promoted
            self._sync_catalog(promoted.model_id)
        self._promotions.record_transition(
            model_id=promoted.model_id,
            version_id=version_id,
            from_stage=from_stage,
            to_stage=to_stage,
        )
        return promoted

    def archive(self, model_id: str) -> RegisteredModel:
        model = self.lookup(model_id)
        archived = model.model_copy(update={"status": ModelStatus.DEPRECATED})
        with self._lock:
            self._models[model_id] = archived
            self._sync_catalog(model_id)
        return archived

    def lookup(self, model_id: str) -> RegisteredModel:
        with self._lock:
            model = self._models.get(model_id)
        if model is None:
            raise ModelNotFoundError(model_id)
        return model

    def latest(self, model_id: str) -> ModelVersion:
        model = self.lookup(model_id)
        if model.latest_version_id is None:
            msg = f"No versions registered for model {model_id}"
            raise ModelVersionNotFoundError(msg)
        return self._get_version(model.latest_version_id)

    def versions(self, model_id: str) -> tuple[ModelVersion, ...]:
        with self._lock:
            if model_id not in self._models:
                raise ModelNotFoundError(model_id)
            version_ids = self._versions_by_model.get(model_id, ())
            return tuple(self._versions[vid] for vid in version_ids if vid in self._versions)

    def get_version(self, version_id: str) -> ModelVersion:
        return self._get_version(version_id)

    def list_models(self) -> tuple[RegisteredModel, ...]:
        with self._lock:
            return tuple(self._models[mid] for mid in sorted(self._models))

    def _get_version(self, version_id: str) -> ModelVersion:
        with self._lock:
            version = self._versions.get(version_id)
        if version is None:
            raise ModelVersionNotFoundError(version_id)
        return version

    def _sync_catalog(self, model_id: str) -> None:
        model = self._models[model_id]
        version_ids = self._versions_by_model.get(model_id, ())
        versions = tuple(self._versions[vid] for vid in version_ids if vid in self._versions)
        self._catalog.upsert(model, versions)

    @staticmethod
    def new_version_id() -> str:
        return f"model-version-{uuid4()}"

    @staticmethod
    def build_version(
        *,
        model_id: str,
        semantic_version: str,
        artifact_id: str,
        dataset_id: str,
        experiment_id: str,
        run_id: str,
        job_id: str,
        config_hash: str,
        checksum: str,
        dataset_snapshot_id: str | None = None,
        stage: ModelStage = ModelStage.DRAFT,
    ) -> ModelVersion:
        return ModelVersion(
            version_id=ModelRegistryStore.new_version_id(),
            model_id=model_id,
            semantic_version=semantic_version,
            artifact_id=artifact_id,
            dataset_id=dataset_id,
            dataset_snapshot_id=dataset_snapshot_id,
            experiment_id=experiment_id,
            run_id=run_id,
            job_id=job_id,
            config_hash=config_hash,
            checksum=checksum,
            stage=stage,
            created_at=utc_now(),
        )
