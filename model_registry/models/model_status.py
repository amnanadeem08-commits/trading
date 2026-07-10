"""Model status definitions."""

from __future__ import annotations

from enum import StrEnum


class ModelStatus(StrEnum):
    """Operational status for a registered model."""

    ACTIVE = "active"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"
    DELETED = "deleted"

    def is_available(self) -> bool:
        return self == ModelStatus.ACTIVE
