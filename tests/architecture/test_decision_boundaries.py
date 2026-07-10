"""Architecture tests for decision layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, PIPELINE_PACKAGES, RULE_IDS


@pytest.mark.architecture
def test_decision_package_is_in_pipeline_layers() -> None:
    assert "decision" in PIPELINE_PACKAGES


@pytest.mark.architecture
def test_decision_forbidden_imports_are_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["decision"]
    assert "risk" in forbidden
    assert "execution" in forbidden
    assert "connectors" in forbidden
    assert "api" in forbidden
    assert "dashboard" in forbidden
    assert "research" in forbidden


@pytest.mark.architecture
def test_decision_boundary_rule_id() -> None:
    assert RULE_IDS["decision_boundary"] == "R11"


@pytest.mark.architecture
def test_decision_does_not_import_risk_or_execution(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "decision_boundary"}
        and violation.file_path.startswith("decision/")
        and (
            "decision must not import risk" in violation.detail
            or "decision must not import execution" in violation.detail
        )
    ]
    assert violations == []


@pytest.mark.architecture
def test_decision_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    decision_files = [item for item in source_files if item.package == "decision"]
    assert decision_files
    module_names = {item.relative_path for item in decision_files}
    assert "decision/__init__.py" in module_names
    assert "decision/orchestration/decision_orchestrator.py" in module_names
    assert "decision/lifecycle/decision_lifecycle_manager.py" in module_names
