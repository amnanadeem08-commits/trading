"""Architecture tests for local filesystem resolution delegation."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

LOCAL_PROVIDER = Path("storage_providers/providers/local_provider.py")
ARTIFACT_RESOLVER = Path("artifact_management/resolver/artifact_resolver.py")


@pytest.mark.architecture
def test_local_provider_does_not_import_ml_frameworks() -> None:
    tree = ast.parse(LOCAL_PROVIDER.read_text(encoding="utf-8"))
    forbidden = {"tensorflow", "torch", "onnx", "sklearn", "boto3", "requests"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root not in forbidden
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            assert root not in forbidden


@pytest.mark.architecture
def test_artifact_resolver_still_delegates_location_to_storage_provider() -> None:
    content = ARTIFACT_RESOLVER.read_text(encoding="utf-8")
    assert "reference.location is None" in content
    assert "storage provider bridge" in content


@pytest.mark.architecture
def test_local_provider_uses_path_sandbox() -> None:
    content = LOCAL_PROVIDER.read_text(encoding="utf-8")
    assert "PathSandbox" in content
    assert "resolve_uri_to_path" in content
