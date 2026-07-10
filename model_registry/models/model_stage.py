"""Model stage definitions."""

from __future__ import annotations

from enum import StrEnum


class ModelStage(StrEnum):
    """Promotion stage for a model version."""

    DRAFT = "draft"
    STAGING = "staging"
    VALIDATION = "validation"
    APPROVED = "approved"
    PRODUCTION = "production"
    ARCHIVED = "archived"

    def next_stage(self) -> ModelStage | None:
        transitions = {
            ModelStage.DRAFT: ModelStage.STAGING,
            ModelStage.STAGING: ModelStage.VALIDATION,
            ModelStage.VALIDATION: ModelStage.APPROVED,
            ModelStage.APPROVED: ModelStage.PRODUCTION,
            ModelStage.PRODUCTION: ModelStage.ARCHIVED,
        }
        return transitions.get(self)

    def is_terminal(self) -> bool:
        return self in {ModelStage.PRODUCTION, ModelStage.ARCHIVED}
