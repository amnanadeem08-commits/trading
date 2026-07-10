"""Artifact manifest contracts."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class ArtifactManifest(PlatformModel):
    """Declarative manifest for artifact contents and dependencies."""

    artifact_id: str
    name: str
    version: str
    engine_type: str = ""
    files: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    runtime_metadata: dict[str, object] = Field(default_factory=dict)
    compatibility_metadata: dict[str, object] = Field(default_factory=dict)
    attributes: dict[str, object] = Field(default_factory=dict)
