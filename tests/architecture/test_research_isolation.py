"""Architecture tests for research isolation."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import PRODUCTION_PACKAGES, RESEARCH_PACKAGE


@pytest.mark.architecture
def test_production_packages_exclude_research() -> None:
    assert RESEARCH_PACKAGE not in PRODUCTION_PACKAGES


@pytest.mark.architecture
def test_production_must_not_import_research(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "research_isolation"
        and "must not import research" in violation.detail
    ]
    assert violations == []


@pytest.mark.architecture
def test_research_package_is_interface_only(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "research_isolation"
        and violation.file_path.startswith("research/")
    ]
    assert violations == []


@pytest.mark.architecture
def test_api_must_not_import_research_rule_exists() -> None:
    from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS

    assert RESEARCH_PACKAGE in FORBIDDEN_IMPORT_PAIRS["api"]
