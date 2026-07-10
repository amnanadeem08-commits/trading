"""Unit tests for model promotion."""

from __future__ import annotations

import pytest

from model_registry import ModelStage, PromotionError, RegistryValidationError
from tests.model_registry_helpers import seed_trained_model


@pytest.mark.unit
def test_promote_through_stages() -> None:
    runtime = seed_trained_model(approval_required=False)
    version = runtime.registry.latest("model-1")
    promoted = runtime.registry.promote(version_id=version.version_id, to_stage=ModelStage.STAGING)
    assert promoted.stage == ModelStage.STAGING
    history = runtime.registry.promotion_registry.history(version.version_id)
    assert len(history) == 1


@pytest.mark.unit
def test_invalid_promotion_rejected() -> None:
    runtime = seed_trained_model(approval_required=False)
    version = runtime.registry.latest("model-1")
    with pytest.raises(RegistryValidationError):
        runtime.registry.promote(version_id=version.version_id, to_stage=ModelStage.PRODUCTION)


@pytest.mark.unit
def test_promotion_with_approval_workflow() -> None:
    runtime = seed_trained_model(approval_required=True)
    version = runtime.registry.latest("model-1")
    staging = runtime.registry.promote(version_id=version.version_id, to_stage=ModelStage.STAGING)
    validation = runtime.registry.promote(
        version_id=staging.version_id,
        to_stage=ModelStage.VALIDATION,
    )
    approved = runtime.promote_version(
        version_id=validation.version_id,
        to_stage=ModelStage.APPROVED,
        approved=True,
    )
    assert approved.stage == ModelStage.APPROVED


@pytest.mark.unit
def test_promotion_rejection() -> None:
    runtime = seed_trained_model(approval_required=True)
    version = runtime.registry.latest("model-1")
    runtime.registry.promote(version_id=version.version_id, to_stage=ModelStage.STAGING)
    validation = runtime.registry.promote(
        version_id=version.version_id,
        to_stage=ModelStage.VALIDATION,
    )
    with pytest.raises(PromotionError):
        runtime.promote_version(
            version_id=validation.version_id,
            to_stage=ModelStage.APPROVED,
            approved=False,
        )
