"""Service registration decorators."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from services.service import BaseService

ServiceType = TypeVar("ServiceType", bound=type[BaseService])

_SERVICE_REGISTRY_KEY = "_platform_service_metadata"


def service(
    *,
    name: str | None = None,
    auto_register: bool = True,
) -> Callable[[ServiceType], ServiceType]:
    """Mark a service class for discovery and optional auto-registration."""

    def decorator(cls: ServiceType) -> ServiceType:
        setattr(
            cls,
            _SERVICE_REGISTRY_KEY,
            {
                "name": name,
                "auto_register": auto_register,
            },
        )
        return cls

    return decorator


def service_metadata(service_type: type[BaseService]) -> dict[str, str | bool | None]:
    """Return discovery metadata attached to a service class."""
    metadata = getattr(service_type, _SERVICE_REGISTRY_KEY, None)
    if metadata is None:
        return {"name": None, "auto_register": False}
    return dict(metadata)
