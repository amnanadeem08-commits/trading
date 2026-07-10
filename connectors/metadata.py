"""Connector metadata for audit and versioning."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel, VersionInfo


class ConnectorMetadata(PlatformModel):
    """Metadata exposed by every connector plugin."""

    connector_name: str = Field(min_length=1)
    connector_version: VersionInfo
    provider: str = Field(min_length=1, description="Data or execution provider name")
    api_version: str = Field(min_length=1)
    supported_assets: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Asset classes supported by this connector",
    )
