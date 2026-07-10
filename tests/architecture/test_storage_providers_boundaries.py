"""Architecture tests for storage provider boundaries."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, RULE_IDS

STORAGE_PROVIDERS_MODULE_ROOT = Path("storage_providers")

FORBIDDEN_TERMS = (
    "websocket",
    "aiohttp",
    "urllib",
    "socket",
    "pmex",
    "crypto",
    "binance",
    "broker",
    "exchange",
    "boto3",
    "requests",
)

TECHNICAL_TERM_PATTERNS = (
    re.compile(r"\btensorflow\b"),
    re.compile(r"\bpytorch\b"),
    re.compile(r"\bsklearn\b"),
    re.compile(r"\bonnx\b"),
    re.compile(r"\bxgboost\b"),
    re.compile(r"\blightgbm\b"),
    re.compile(r"\bcatboost\b"),
    re.compile(r"\bpredict\b"),
    re.compile(r"\bportfolio\b"),
)

TERM_SCAN_EXCLUDED_FILES = frozenset(
    {
        "storage_providers/contracts/provider_type.py",
        "storage_providers/resolver/provider_resolver.py",
    }
)


def _iter_storage_providers_source_files() -> list[Path]:
    return sorted(STORAGE_PROVIDERS_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_storage_providers_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "storage_providers/integration/artifact_management_bridge.py" in module_names
    assert "storage_providers/contracts/storage_provider.py" in module_names
    assert "storage_providers/registry/provider_registry.py" in module_names


@pytest.mark.architecture
def test_storage_providers_do_not_import_forbidden_packages() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["storage_providers"]
    for path in _iter_storage_providers_source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root not in forbidden, f"{path} imports {root}"
            elif isinstance(node, ast.ImportFrom) and node.module:
                root = node.module.split(".")[0]
                assert root not in forbidden, f"{path} imports {root}"


@pytest.mark.architecture
def test_storage_providers_avoid_forbidden_terms() -> None:
    for path in _iter_storage_providers_source_files():
        relative = path.as_posix()
        if relative in TERM_SCAN_EXCLUDED_FILES:
            continue
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"
        for pattern in TECHNICAL_TERM_PATTERNS:
            assert (
                pattern.search(content) is None
            ), f"{path} contains forbidden pattern '{pattern.pattern}'"


@pytest.mark.architecture
def test_storage_providers_public_exports() -> None:
    from storage_providers import (
        ArtifactManagementStorageBridge,
        StorageProvider,
        build_storage_bridge,
    )

    assert StorageProvider is not None
    assert ArtifactManagementStorageBridge is not None
    assert callable(build_storage_bridge)


@pytest.mark.architecture
def test_artifact_management_does_not_import_storage_providers(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("artifact_management/")
        and "storage_providers" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_storage_providers_boundary_rule_registered() -> None:
    assert "storage_providers_boundary" in RULE_IDS


@pytest.mark.architecture
def test_storage_providers_sits_between_artifact_management_and_ml() -> None:
    from architecture.dependency_rules import PIPELINE_PACKAGES

    artifacts_layer = PIPELINE_PACKAGES["artifact_management"]
    storage_layer = PIPELINE_PACKAGES["storage_providers"]
    ml_layer = PIPELINE_PACKAGES["ml"]
    assert storage_layer > artifacts_layer
    assert ml_layer > storage_layer
