"""Architecture tests confirming artifact management delegates URI resolution."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

ARTIFACT_RESOLVER = Path("artifact_management/resolver/artifact_resolver.py")
FRAMEWORK_BRIDGE = Path("artifact_management/integration/framework_adapter_bridge.py")


@pytest.mark.architecture
def test_artifact_resolver_does_not_import_uri_resolver() -> None:
    tree = ast.parse(ARTIFACT_RESOLVER.read_text(encoding="utf-8"))
    import_from = {
        node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module
    }
    import_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    assert "artifact_management.resolver.uri_resolver" not in import_from
    assert "URIResolver" not in import_names


@pytest.mark.architecture
def test_artifact_resolver_requires_provider_location() -> None:
    content = ARTIFACT_RESOLVER.read_text(encoding="utf-8")
    assert "storage provider bridge" in content
    assert "reference.location is None" in content


@pytest.mark.architecture
def test_framework_adapter_bridge_requires_storage_resolution() -> None:
    content = FRAMEWORK_BRIDGE.read_text(encoding="utf-8")
    assert "storage provider bridge" in content
    assert "reference.location is None" in content


@pytest.mark.architecture
def test_artifact_validator_does_not_check_supported_schemes() -> None:
    validator_path = Path("artifact_management/validation/validator.py")
    content = validator_path.read_text(encoding="utf-8")
    assert "SUPPORTED_SCHEMES" not in content
