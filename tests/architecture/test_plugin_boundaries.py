"""Architecture tests for plugin layer boundaries."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS, ORCHESTRATION_PACKAGES


@pytest.mark.architecture
def test_plugins_in_orchestration_packages() -> None:
    assert "plugins" in ORCHESTRATION_PACKAGES


@pytest.mark.architecture
def test_plugins_forbidden_imports_defined() -> None:
    forbidden = FORBIDDEN_IMPORT_PAIRS["plugins"]
    assert "connectors" in forbidden
    assert "ml" in forbidden
    assert "ai" in forbidden
    assert "llm" in forbidden
    assert "risk" in forbidden
    assert "execution" in forbidden


@pytest.mark.architecture
def test_plugins_does_not_import_connectors(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "plugins_boundary"
        and "plugins must not import connectors" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_plugins_has_no_market_branching(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "plugins_boundary"
        and "market-specific branching" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_plugins_package_exists(validator) -> None:
    source_files = validator._load_source_files()
    plugin_files = [item for item in source_files if item.package == "plugins"]
    assert plugin_files
