"""Architecture tests for artifact management boundaries."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, RULE_IDS

ARTIFACT_MANAGEMENT_MODULE_ROOT = Path("artifact_management")

FORBIDDEN_TERMS = (
    "http",
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
        "artifact_management/models/artifact_location.py",
    }
)


def _iter_artifact_management_source_files() -> list[Path]:
    return sorted(ARTIFACT_MANAGEMENT_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_artifact_management_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "artifact_management/integration/framework_adapter_bridge.py" in module_names
    assert "artifact_management/models/artifact_reference.py" in module_names
    assert "artifact_management/registry/artifact_registry.py" in module_names


@pytest.mark.architecture
def test_artifact_management_do_not_import_forbidden_packages() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["artifact_management"]
    for path in _iter_artifact_management_source_files():
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
def test_artifact_management_avoid_forbidden_terms() -> None:
    for path in _iter_artifact_management_source_files():
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
def test_artifact_management_public_exports() -> None:
    from artifact_management import (
        ArtifactReference,
        FrameworkAdapterArtifactBridge,
        build_artifact_bridge,
    )

    assert ArtifactReference is not None
    assert FrameworkAdapterArtifactBridge is not None
    assert callable(build_artifact_bridge)


@pytest.mark.architecture
def test_framework_adapters_does_not_import_artifact_management(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("framework_adapters/")
        and "artifact_management" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_artifact_management_boundary_rule_registered() -> None:
    assert "artifact_management_boundary" in RULE_IDS


@pytest.mark.architecture
def test_artifact_management_sits_between_framework_adapters_and_storage_providers() -> None:
    from architecture.dependency_rules import PIPELINE_PACKAGES

    adapters_layer = PIPELINE_PACKAGES["framework_adapters"]
    artifacts_layer = PIPELINE_PACKAGES["artifact_management"]
    storage_layer = PIPELINE_PACKAGES["storage_providers"]
    assert artifacts_layer > adapters_layer
    assert storage_layer > artifacts_layer
