"""Architecture tests for ML layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, PIPELINE_PACKAGES, RULE_IDS


@pytest.mark.architecture
def test_ml_package_is_in_pipeline_layers() -> None:
    assert "ml" in PIPELINE_PACKAGES


@pytest.mark.architecture
def test_ml_forbidden_imports_are_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["ml"]
    assert "ai" in forbidden
    assert "llm" in forbidden
    assert "decision" in forbidden
    assert "risk" in forbidden
    assert "execution" in forbidden
    assert "connectors" in forbidden
    assert "api" in forbidden
    assert "dashboard" in forbidden
    assert "research" in forbidden


@pytest.mark.architecture
def test_ml_boundary_rule_id() -> None:
    assert RULE_IDS["ml_boundary"] == "R11"


@pytest.mark.architecture
def test_ml_does_not_import_ai_or_decision(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "ml_boundary"}
        and violation.file_path.startswith("ml/")
        and (
            "ml must not import ai" in violation.detail
            or "ml must not import decision" in violation.detail
        )
    ]
    assert violations == []


@pytest.mark.architecture
def test_ml_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    ml_files = [item for item in source_files if item.package == "ml"]
    assert ml_files
    module_names = {item.relative_path for item in ml_files}
    assert "ml/__init__.py" in module_names
    assert "ml/registry/ml_registry.py" in module_names
    assert "ml/lifecycle/ml_lifecycle_manager.py" in module_names
