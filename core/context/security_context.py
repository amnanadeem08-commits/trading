"""Security context contract."""

from __future__ import annotations

from pydantic import Field

from models.common import PlatformModel


class SecurityContext(PlatformModel):
    """Context describing security metadata for an operation."""

    authentication_method: str = Field(min_length=1, default="internal")
    authorization_scope: str = Field(min_length=1, default="platform")
    token_id: str | None = None
    permissions: tuple[str, ...] = Field(default_factory=tuple)
    attributes: dict[str, str] = Field(default_factory=dict)
