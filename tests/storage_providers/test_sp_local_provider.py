"""Unit tests for local storage provider."""

from __future__ import annotations

import hashlib
import sys
from typing import TYPE_CHECKING

import pytest

from storage_providers import (
    LOCAL_PROVIDER_ID,
    ProviderFilesystemError,
    ProviderPathError,
    ProviderType,
    create_local_provider,
)
from storage_providers.providers.path_sandbox import PathSandbox, PathSandboxConfig
from tests.storage_providers_helpers import write_test_artifact

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.unit
def test_local_provider_contract() -> None:
    provider = create_local_provider(artifact_root=".")
    assert provider.provider_id() == LOCAL_PROVIDER_ID
    assert provider.provider_type() == ProviderType.LOCAL
    assert "local" in provider.manifest().supported_uri_schemes
    assert "file" in provider.manifest().supported_uri_schemes


@pytest.mark.unit
def test_local_provider_resolves_real_file_metadata(tmp_path: Path) -> None:
    relative = "artifacts/stub-model/1.0.0/model.stub"
    content = b"local provider test content"
    write_test_artifact(tmp_path, relative_path=relative, content=content)
    provider = create_local_provider(artifact_root=tmp_path)
    provider.startup()
    provider.validate()

    resolution = provider.resolve(uri=f"local://{relative}")
    metadata = provider.fetch_metadata(uri=f"local://{relative}")

    assert resolution["resolved"] is True
    assert resolution["path"] == relative
    assert metadata["size"] == len(content)
    assert metadata["extension"] == "stub"
    assert metadata["checksum"] == hashlib.sha256(content).hexdigest()
    assert metadata["complete"] is True


@pytest.mark.unit
def test_local_provider_supports_file_scheme(tmp_path: Path) -> None:
    relative = "models/test.bin"
    write_test_artifact(tmp_path, relative_path=relative, content=b"abc")
    provider = create_local_provider(artifact_root=tmp_path)
    metadata = provider.fetch_metadata(uri=f"file://{relative}")
    assert metadata["path"] == relative


@pytest.mark.unit
def test_local_provider_rejects_path_traversal(tmp_path: Path) -> None:
    provider = create_local_provider(artifact_root=tmp_path)
    with pytest.raises(ProviderFilesystemError):
        provider.resolve(uri="local://../outside.txt")


@pytest.mark.unit
def test_local_provider_rejects_missing_file(tmp_path: Path) -> None:
    provider = create_local_provider(artifact_root=tmp_path)
    with pytest.raises(ProviderFilesystemError, match="does not exist"):
        provider.fetch_metadata(uri="local://missing/model.stub")


@pytest.mark.unit
def test_path_sandbox_rejects_symlink_escape(tmp_path: Path) -> None:
    if sys.platform == "win32":
        pytest.skip("symlink creation requires elevated privileges on Windows")
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = artifact_root / "link.stub"
    link.symlink_to(outside)
    sandbox = PathSandbox(PathSandboxConfig(artifact_root=artifact_root, allow_symlinks=False))
    with pytest.raises(ProviderPathError):
        sandbox.resolve_uri_to_path("local://link.stub")


@pytest.mark.unit
def test_local_provider_verify_checksum(tmp_path: Path) -> None:
    relative = "artifacts/check.stub"
    content = b"checksum-test"
    _, checksum = write_test_artifact(tmp_path, relative_path=relative, content=content)
    provider = create_local_provider(artifact_root=tmp_path)
    assert provider.verify_checksum(uri=f"local://{relative}", expected_checksum=checksum) is True
    assert provider.verify_checksum(uri=f"local://{relative}", expected_checksum="bad") is False


@pytest.mark.unit
def test_local_provider_shutdown_clears_metadata_cache(tmp_path: Path) -> None:
    relative = "artifacts/cache.stub"
    write_test_artifact(tmp_path, relative_path=relative, content=b"cached")
    provider = create_local_provider(artifact_root=tmp_path, cache_metadata=True)
    provider.fetch_metadata(uri=f"local://{relative}")
    provider.shutdown()
    provider.startup()
    provider.fetch_metadata(uri=f"local://{relative}")


@pytest.mark.unit
def test_local_provider_validate_rejects_non_directory(tmp_path: Path) -> None:
    file_path = tmp_path / "not-a-dir"
    file_path.write_text("x", encoding="utf-8")
    provider = create_local_provider(artifact_root=file_path)
    with pytest.raises(ProviderFilesystemError):
        provider.validate()


@pytest.mark.unit
def test_local_provider_rejects_directory_path(tmp_path: Path) -> None:
    directory = tmp_path / "folder"
    directory.mkdir()
    provider = create_local_provider(artifact_root=tmp_path)
    with pytest.raises(ProviderFilesystemError, match="not a file"):
        provider.fetch_metadata(uri="local://folder")
