"""Architecture tests for risk layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, PIPELINE_PACKAGES, RULE_IDS


@pytest.mark.architecture
def test_risk_package_is_in_pipeline_layers() -> None:
    assert "risk" in PIPELINE_PACKAGES


@pytest.mark.architecture
def test_risk_forbidden_imports_are_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["risk"]
    assert "execution" in forbidden
    assert "connectors" in forbidden
    assert "api" in forbidden
    assert "dashboard" in forbidden
    assert "research" in forbidden


@pytest.mark.architecture
def test_risk_boundary_rule_id() -> None:
    assert RULE_IDS["risk_boundary"] == "R11"


@pytest.mark.architecture
def test_risk_does_not_import_execution(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "risk_boundary"}
        and violation.file_path.startswith("risk/")
        and "risk must not import execution" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_risk_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    risk_files = [item for item in source_files if item.package == "risk"]
    assert risk_files
    module_names = {item.relative_path for item in risk_files}
    assert "risk/__init__.py" in module_names
    assert "risk/orchestration/risk_orchestrator.py" in module_names
    assert "risk/lifecycle/risk_lifecycle_manager.py" in module_names
