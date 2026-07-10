"""Architecture tests for feature engineering boundaries."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS

FEATURE_MODULE_ROOT = Path("feature_engineering")

FORBIDDEN_TERMS = (
    "http",
    "websocket",
    "requests",
    "aiohttp",
    "urllib",
    "socket",
    "pmex",
    "crypto",
    "binance",
    "broker",
    "exchange",
)

TECHNICAL_TERM_PATTERNS = (
    re.compile(r"\brsi\b"),
    re.compile(r"\bmacd\b"),
    re.compile(r"\bbollinger\b"),
    re.compile(r"\bindicator\b"),
    re.compile(r"\bsignal\b"),
    re.compile(r"\bforecast\b"),
    re.compile(r"\bportfolio\b"),
)


def _iter_feature_source_files() -> list[Path]:
    return sorted(FEATURE_MODULE_ROOT.rglob("*.py"))


@pytest.mark.architecture
def test_feature_engineering_modules_exist(validator) -> None:
    source_files = validator._load_source_files()
    module_names = {item.relative_path for item in source_files}
    assert "feature_engineering/models/feature_vector.py" in module_names
    assert "feature_engineering/extraction/extraction_pipeline.py" in module_names
    assert "feature_engineering/integration/market_data_bridge.py" in module_names
    assert "feature_engineering/registry/feature_registry.py" in module_names


@pytest.mark.architecture
def test_feature_engineering_modules_do_not_import_forbidden_packages() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["feature_engineering"]
    for path in _iter_feature_source_files():
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
def test_feature_engineering_modules_avoid_forbidden_terms() -> None:
    for path in _iter_feature_source_files():
        content = path.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            assert term not in content, f"{path} contains forbidden term '{term}'"
        for pattern in TECHNICAL_TERM_PATTERNS:
            assert (
                pattern.search(content) is None
            ), f"{path} contains forbidden pattern '{pattern.pattern}'"


@pytest.mark.architecture
def test_feature_engineering_public_exports() -> None:
    from feature_engineering import FeatureExtractionPipeline, FeatureRegistry, FeatureVector

    assert FeatureExtractionPipeline.__name__ == "FeatureExtractionPipeline"
    assert FeatureRegistry.__name__ == "FeatureRegistry"
    assert FeatureVector.__name__ == "FeatureVector"


@pytest.mark.architecture
def test_market_data_does_not_import_feature_engineering(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.file_path.startswith("market_data/")
        and "feature_engineering" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_feature_engineering_boundary_rule_registered() -> None:
    from architecture.dependency_rules import RULE_IDS

    assert "feature_engineering_boundary" in RULE_IDS
