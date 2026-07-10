"""Architecture tests for AI layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, PIPELINE_PACKAGES, RULE_IDS


@pytest.mark.architecture
def test_ai_package_is_in_pipeline_layers() -> None:
    assert "ai" in PIPELINE_PACKAGES


@pytest.mark.architecture
def test_ai_forbidden_imports_are_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["ai"]
    assert "decision" in forbidden
    assert "risk" in forbidden
    assert "execution" in forbidden
    assert "connectors" in forbidden
    assert "api" in forbidden
    assert "dashboard" in forbidden
    assert "research" in forbidden


@pytest.mark.architecture
def test_ai_boundary_rule_id() -> None:
    assert RULE_IDS["ai_boundary"] == "R11"


@pytest.mark.architecture
def test_ai_does_not_import_decision_or_risk(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name in {"forbidden_import", "ai_boundary"}
        and violation.file_path.startswith("ai/")
        and (
            "ai must not import decision" in violation.detail
            or "ai must not import risk" in violation.detail
        )
    ]
    assert violations == []


@pytest.mark.architecture
def test_ai_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    ai_files = [item for item in source_files if item.package == "ai"]
    assert ai_files
    module_names = {item.relative_path for item in ai_files}
    assert "ai/__init__.py" in module_names
    assert "ai/orchestration/ai_orchestrator.py" in module_names
    assert "ai/lifecycle/ai_lifecycle_manager.py" in module_names
