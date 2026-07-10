"""Plugin capability contract."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from models.common import PlatformModel


class CapabilityRelations(PlatformModel):
    """Capability dependency metadata for future resolution."""

    provides: tuple[str, ...] = Field(default_factory=tuple)
    requires: tuple[str, ...] = Field(default_factory=tuple)
    optional: tuple[str, ...] = Field(default_factory=tuple)
    conflicts: tuple[str, ...] = Field(default_factory=tuple)


class Capability(PlatformModel):
    """Describes a capability exposed by a plugin."""

    capability_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    version: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    relations: CapabilityRelations = Field(default_factory=CapabilityRelations)
