"""Filesystem path sandbox for local storage providers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from storage_providers.exceptions import ProviderPathError, ProviderResolutionError

_SUPPORTED_SCHEMES = frozenset({"local", "file"})


@dataclass(frozen=True)
class PathSandboxConfig:
    """Configuration for sandboxed filesystem access."""

    artifact_root: Path
    allow_symlinks: bool = False
    follow_links: bool = False


def parse_storage_uri(uri: str) -> tuple[str, str]:
    """Parse a storage URI into scheme and relative remainder."""
    if "://" not in uri:
        msg = f"URI must include a scheme: {uri}"
        raise ProviderResolutionError(msg)
    scheme, remainder = uri.split("://", 1)
    normalized_scheme = scheme.strip().lower()
    if normalized_scheme not in _SUPPORTED_SCHEMES:
        msg = f"Unsupported URI scheme for local provider: {normalized_scheme}"
        raise ProviderResolutionError(msg)
    if not remainder.strip():
        msg = f"URI path must not be empty: {uri}"
        raise ProviderResolutionError(msg)
    return normalized_scheme, remainder


def normalize_relative_path(relative_path: str) -> str:
    """Normalize a relative path and reject traversal segments."""
    if ".." in Path(relative_path).parts:
        msg = "Path traversal is not allowed"
        raise ProviderPathError(msg)
    normalized = Path(relative_path.lstrip("/")).as_posix()
    if normalized in {"", "."}:
        msg = "Resolved path must not be empty"
        raise ProviderPathError(msg)
    return normalized


def _resolve_without_symlinks(path: Path) -> Path:
    current = Path(path.anchor).resolve() if path.anchor else Path.cwd().resolve()
    for part in path.parts:
        if part in {path.anchor, ""}:
            continue
        if part == "..":
            msg = "Path traversal is not allowed"
            raise ProviderPathError(msg)
        if part == ".":
            continue
        current = current / part
        if current.is_symlink():
            msg = "Symlink escape is not allowed"
            raise ProviderPathError(msg)
    return current


def _is_within_root(path: Path, root: Path, *, follow_links: bool) -> bool:
    root_resolved = root.resolve()
    try:
        resolved = path.resolve() if follow_links else _resolve_without_symlinks(path)
    except ProviderPathError:
        raise
    except OSError as error:
        msg = f"Unable to resolve path: {path}"
        raise ProviderPathError(msg) from error
    if resolved == root_resolved:
        return True
    return root_resolved in resolved.parents


class PathSandbox:
    """Validates and resolves artifact URIs within a configured root."""

    def __init__(self, config: PathSandboxConfig) -> None:
        self._config = config
        self._root = config.artifact_root.resolve()
        if not self._root.exists():
            self._root.mkdir(parents=True, exist_ok=True)

    @property
    def artifact_root(self) -> Path:
        return self._root

    def resolve_uri_to_path(self, uri: str) -> Path:
        """Resolve a local or file URI to a sandboxed filesystem path."""
        scheme, remainder = parse_storage_uri(uri)
        _ = scheme
        relative = normalize_relative_path(remainder)
        candidate = self._root / relative
        if not self._config.allow_symlinks and candidate.is_symlink():
            msg = "Symlink paths are not allowed"
            raise ProviderPathError(msg)
        if not _is_within_root(
            candidate,
            self._root,
            follow_links=self._config.follow_links,
        ):
            msg = f"Path escapes artifact root: {relative}"
            raise ProviderPathError(msg)
        return (
            candidate.resolve()
            if self._config.follow_links
            else _resolve_without_symlinks(candidate)
        )

    def relative_path(self, path: Path) -> str:
        """Return the path relative to the artifact root."""
        return path.relative_to(self._root).as_posix()
