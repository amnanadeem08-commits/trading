"""Unit tests for path sandbox utilities."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from storage_providers.exceptions import ProviderPathError
from storage_providers.providers.path_sandbox import (
    PathSandbox,
    PathSandboxConfig,
    normalize_relative_path,
    parse_storage_uri,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_parse_storage_uri_accepts_local_and_file() -> None:
    assert parse_storage_uri("local://artifacts/model.stub") == ("local", "artifacts/model.stub")
    assert parse_storage_uri("file://models/test.bin") == ("file", "models/test.bin")


@pytest.mark.unit
def test_normalize_relative_path_strips_leading_slash() -> None:
    assert normalize_relative_path("/artifacts/model.stub") == "artifacts/model.stub"


@pytest.mark.unit
def test_normalize_relative_path_rejects_dot_and_empty() -> None:
    with pytest.raises(ProviderPathError):
        normalize_relative_path(".")
    with pytest.raises(ProviderPathError):
        normalize_relative_path("")


@pytest.mark.unit
def test_normalize_relative_path_rejects_traversal() -> None:
    with pytest.raises(ProviderPathError):
        normalize_relative_path("../outside.txt")


@pytest.mark.unit
def test_path_sandbox_relative_path(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    file_path = root / "models" / "test.stub"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("x", encoding="utf-8")
    sandbox = PathSandbox(PathSandboxConfig(artifact_root=root))
    resolved = sandbox.resolve_uri_to_path("local://models/test.stub")
    assert sandbox.relative_path(resolved) == "models/test.stub"


@pytest.mark.unit
def test_path_sandbox_follow_links_when_enabled(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    file_path = root / "model.stub"
    file_path.write_text("content", encoding="utf-8")
    sandbox = PathSandbox(
        PathSandboxConfig(artifact_root=root, follow_links=True, allow_symlinks=True)
    )
    resolved = sandbox.resolve_uri_to_path("local://model.stub")
    assert resolved.exists()


@pytest.mark.unit
def test_path_sandbox_rejects_escape_via_absolute_path(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    sandbox = PathSandbox(PathSandboxConfig(artifact_root=root))
    with pytest.raises(ProviderPathError):
        sandbox.resolve_uri_to_path(f"local://{outside.as_posix()}")


@pytest.mark.unit
def test_path_sandbox_allows_symlink_when_configured(tmp_path: Path) -> None:
    if sys.platform == "win32":
        pytest.skip("symlink creation requires elevated privileges on Windows")
    root = tmp_path / "artifacts"
    root.mkdir()
    target = root / "target.stub"
    target.write_text("data", encoding="utf-8")
    link = root / "link.stub"
    link.symlink_to(target)
    sandbox = PathSandbox(PathSandboxConfig(artifact_root=root, allow_symlinks=True))
    resolved = sandbox.resolve_uri_to_path("local://link.stub")
    assert resolved.read_text(encoding="utf-8") == "data"
