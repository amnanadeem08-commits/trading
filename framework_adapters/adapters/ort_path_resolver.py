"""Resolve model paths from storage-provider artifact metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from framework_adapters.exceptions import AdapterLoadError


def resolve_model_path(
    *,
    artifact_reference: str,
    metadata: dict[str, object],
    fallback_path: Path | None = None,
) -> Path:
    """Resolve a filesystem path from artifact metadata supplied by storage bridge."""
    location = metadata.get("location")
    if isinstance(location, dict):
        path = _path_from_location(location)
        if path is not None:
            return path

    provider_resolution = metadata.get("provider_resolution")
    if isinstance(provider_resolution, dict):
        path = _path_from_provider_resolution(provider_resolution)
        if path is not None:
            return path

    if fallback_path is not None and fallback_path.exists():
        return fallback_path

    msg = f"Unable to resolve model path for artifact: {artifact_reference}"
    raise AdapterLoadError(msg)


def _path_from_location(location: dict[str, object]) -> Path | None:
    relative = str(location.get("path", "")).strip()
    if not relative:
        return None
    attributes = location.get("attributes")
    if isinstance(attributes, dict):
        root = attributes.get("artifact_root")
        if root:
            return Path(str(root)) / relative
    return None


def _path_from_provider_resolution(resolution: dict[str, Any]) -> Path | None:
    relative = str(resolution.get("path", "")).strip()
    root = resolution.get("artifact_root")
    if relative and root:
        return Path(str(root)) / relative
    return None
