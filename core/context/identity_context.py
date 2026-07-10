"""Identity context contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class IdentityContext(PlatformModel):
    """Context describing the actor initiating an operation."""

    principal_id: str = Field(min_length=1, default="system")
    principal_type: str = Field(min_length=1, default="service")
    session_id: str | None = None
    roles: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
