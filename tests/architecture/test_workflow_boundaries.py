"""Architecture tests for workflow layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, ORCHESTRATION_PACKAGES


@pytest.mark.architecture
def test_workflow_in_orchestration_packages() -> None:
    assert "workflow" in ORCHESTRATION_PACKAGES


@pytest.mark.architecture
def test_workflow_forbidden_imports_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["workflow"]
    assert "connectors" in forbidden
    assert "ml" in forbidden
    assert "ai" in forbidden
    assert "risk" in forbidden
    assert "execution" in forbidden


@pytest.mark.architecture
def test_workflow_does_not_import_connectors(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "workflow_boundary"
        and "workflow must not import connectors" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_workflow_has_no_market_branching(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "workflow_boundary"
        and "market-specific branching" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_workflow_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    workflow_files = [item for item in source_files if item.package == "workflow"]
    assert workflow_files
    module_names = {item.relative_path for item in workflow_files}
    assert "workflow/__init__.py" in module_names
    assert "workflow/runtime.py" in module_names
    assert "workflow/executor.py" in module_names
