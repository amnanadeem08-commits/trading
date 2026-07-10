"""Architecture tests for governance and layer rule enforcement."""

from __future__ import annotations

import ast

import pytest

from architecture.dependency_rules import GOVERNANCE_PACKAGES, RULE_IDS
from architecture.reporting import format_report, format_summary
from architecture.validators import ArchitectureValidator
from tests.architecture.conftest import PROJECT_ROOT


@pytest.mark.architecture
def test_governance_packages_avoid_forbidden_dependencies(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "layer_rule"
    ]
    assert violations == []


@pytest.mark.architecture
def test_rule_ids_are_mapped() -> None:
    assert RULE_IDS["research_isolation"] == "R9"
    assert RULE_IDS["dependency_direction"] == "R11"


@pytest.mark.architecture
def test_architecture_report_passes_for_current_codebase(architecture_report) -> None:
    assert architecture_report.violations == ()
    assert "PASS" in format_report(architecture_report)
    assert format_summary(architecture_report) == "PASS"


@pytest.mark.architecture
def test_validator_detects_reverse_pipeline_import() -> None:
    source = "from ml import trainer\n"
    tree = ast.parse(source)
    validator = ArchitectureValidator(PROJECT_ROOT)
    synthetic = type(
        "SyntheticSource",
        (),
        {
            "path": PROJECT_ROOT / "data" / "pipeline.py",
            "relative_path": "data/pipeline.py",
            "package": "data",
            "source": source,
            "tree": tree,
        },
    )()
    violations = validator._validate_dependency_direction([synthetic])
    assert len(violations) == 1
    assert "must not import ml" in violations[0].detail


@pytest.mark.architecture
def test_validator_detects_market_branching_in_services() -> None:
    source = "if market == 'binance':\n    pass\n"
    tree = ast.parse(source)
    validator = ArchitectureValidator(PROJECT_ROOT)
    synthetic = type(
        "SyntheticSource",
        (),
        {
            "path": PROJECT_ROOT / "services" / "router.py",
            "relative_path": "services/router.py",
            "package": "services",
            "source": source,
            "tree": tree,
        },
    )()
    violations = validator._validate_service_boundaries([synthetic])
    assert len(violations) == 1
    assert violations[0].detail == "market-specific branching is forbidden"


@pytest.mark.architecture
def test_governance_package_list_is_complete() -> None:
    assert frozenset({"events", "versioning", "audit", "feature_flags"}) == GOVERNANCE_PACKAGES
