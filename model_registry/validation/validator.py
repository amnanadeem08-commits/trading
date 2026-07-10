"""Model registry validator."""

from __future__ import annotations

from model_registry.approval.approval_policy import ApprovalPolicy
from model_registry.exceptions import RegistryValidationError
from model_registry.models.model_stage import ModelStage
from model_registry.models.model_version import ModelVersion
from model_registry.models.registered_model import RegisteredModel
from model_registry.validation.validation_result import RegistryValidationResult


class RegistryValidator:
    """Validates registry operations and promotion transitions."""

    def __init__(self, *, policy: ApprovalPolicy | None = None) -> None:
        self._policy = policy or ApprovalPolicy(
            policy_id="default",
            name="Default Promotion Policy",
        )

    @property
    def policy(self) -> ApprovalPolicy:
        return self._policy

    def validate_model(self, model: RegisteredModel) -> RegistryValidationResult:
        errors: list[str] = []
        if not model.model_id.strip():
            errors.append("model_id must not be empty")
        if not model.metadata.name.strip():
            errors.append("model name must not be empty")
        if errors:
            return RegistryValidationResult.failure(*errors, model_id=model.model_id)
        return RegistryValidationResult.success(model_id=model.model_id)

    def validate_version(
        self,
        version: ModelVersion,
        *,
        existing_versions: tuple[ModelVersion, ...] = (),
    ) -> RegistryValidationResult:
        errors: list[str] = []
        if not version.version_id.strip():
            errors.append("version_id must not be empty")
        if not version.artifact_id.strip():
            errors.append("artifact_id must not be empty")
        if not version.dataset_id.strip():
            errors.append("dataset_id must not be empty")
        if not version.checksum.strip():
            errors.append("checksum must not be empty")
        for existing in existing_versions:
            if existing.version_id != version.version_id and existing.checksum == version.checksum:
                errors.append(f"duplicate checksum for version {existing.version_id}")
        if errors:
            return RegistryValidationResult.failure(*errors, model_id=version.model_id)
        return RegistryValidationResult.success(
            model_id=version.model_id,
            version_id=version.version_id,
        )

    def validate_promotion(
        self,
        *,
        version: ModelVersion,
        to_stage: ModelStage,
        approval_required: bool = True,
    ) -> RegistryValidationResult:
        if version.stage == to_stage:
            return RegistryValidationResult.failure(
                f"version already at stage {to_stage.value}",
                model_id=version.model_id,
            )
        if not self._policy.allows(from_stage=version.stage, to_stage=to_stage):
            return RegistryValidationResult.failure(
                f"invalid promotion from {version.stage.value} to {to_stage.value}",
                model_id=version.model_id,
            )
        if approval_required and to_stage in {ModelStage.APPROVED, ModelStage.PRODUCTION}:
            warnings = ("approval workflow required",)
            return RegistryValidationResult.success(
                model_id=version.model_id,
                version_id=version.version_id,
                warnings=warnings,
            )
        return RegistryValidationResult.success(
            model_id=version.model_id,
            version_id=version.version_id,
        )

    def ensure_valid(self, result: RegistryValidationResult) -> None:
        if not result.valid:
            message = result.errors[0] if result.errors else "validation failed"
            raise RegistryValidationError(message)
