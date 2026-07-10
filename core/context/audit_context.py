"""Audit context contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, ReproducibilityKey


class AuditContext(PlatformModel):
    """Context describing audit metadata for an operation."""

    audit_id: str = Field(min_length=1)
    actor_id: str = Field(min_length=1, default="system")
    action: str = Field(min_length=1)
    resource_type: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    dataset_ids: tuple[str, ...] = Field(default_factory=tuple)
    plugin_ids: tuple[str, ...] = Field(default_factory=tuple)
    component_versions: dict[str, str] = Field(default_factory=dict)
    reproducibility: ReproducibilityKey | None = None
    attributes: dict[str, str] = Field(default_factory=dict)
