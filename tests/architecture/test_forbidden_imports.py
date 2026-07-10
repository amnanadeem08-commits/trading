"""Architecture tests for forbidden import pairs."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import FORBIDDEN_IMPORT_PAIRS


@pytest.mark.architecture
def test_forbidden_import_rules_are_defined() -> None:
    assert "services" in FORBIDDEN_IMPORT_PAIRS
    assert "connectors" in FORBIDDEN_IMPORT_PAIRS["services"]
    assert "ai" in FORBIDDEN_IMPORT_PAIRS["ml"]
    assert "decision" in FORBIDDEN_IMPORT_PAIRS["ai"]
    assert "connectors" in FORBIDDEN_IMPORT_PAIRS["ml"]
    assert "connectors" in FORBIDDEN_IMPORT_PAIRS["decision"]
    assert "connectors" in FORBIDDEN_IMPORT_PAIRS["risk"]
    assert "research" in FORBIDDEN_IMPORT_PAIRS["api"]


@pytest.mark.architecture
def test_no_forbidden_import_violations(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "forbidden_import"
    ]
    assert violations == []


@pytest.mark.architecture
def test_core_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["core"]
    assert blocked == frozenset(
        {
            "ai",
            "connectors",
            "ml",
            "llm",
            "decision",
            "risk",
            "execution",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_ml_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["ml"]
    assert blocked == frozenset(
        {
            "ai",
            "llm",
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_ai_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["ai"]
    assert blocked == frozenset(
        {
            "decision",
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_decision_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["decision"]
    assert blocked == frozenset(
        {
            "risk",
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_risk_must_not_import_forbidden_layers() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["risk"]
    assert blocked == frozenset(
        {
            "execution",
            "connectors",
            "api",
            "dashboard",
            "research",
        }
    )


@pytest.mark.architecture
def test_services_must_not_import_connectors_directly() -> None:
    blocked = FORBIDDEN_IMPORT_PAIRS["services"]
    assert blocked == frozenset({"connectors"})
