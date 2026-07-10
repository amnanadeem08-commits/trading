"""Unit tests for architecture reporting helpers."""

from __future__ import annotations

import pytest

from architecture.reporting import format_report, format_summary, format_violation
from architecture.validators import ArchitectureReport, Violation


@pytest.mark.unit
def test_format_violation_includes_rule_and_location() -> None:
    violation = Violation(
        rule_id="R9",
        rule_name="research_isolation",
        file_path="models/example.py",
        detail="models must not import research",
        line_number=12,
    )
    rendered = format_violation(violation)
    assert "[R9]" in rendered
    assert "models/example.py:12" in rendered
    assert "must not import research" in rendered


@pytest.mark.unit
def test_format_report_pass() -> None:
    report = ArchitectureReport(files_scanned=10, violations=())
    rendered = format_report(report)
    assert "PASS" in rendered
    assert "Files scanned: 10" in rendered


@pytest.mark.unit
def test_format_report_fail() -> None:
    violation = Violation(
        rule_id="R11",
        rule_name="dependency_direction",
        file_path="data/pipeline.py",
        detail="reverse import",
    )
    report = ArchitectureReport(files_scanned=3, violations=(violation,))
    rendered = format_report(report)
    assert "FAIL" in rendered
    assert "dependency_direction" in rendered


@pytest.mark.unit
def test_format_summary_pass_and_fail() -> None:
    pass_report = ArchitectureReport(files_scanned=1, violations=())
    fail_report = ArchitectureReport(
        files_scanned=1,
        violations=(
            Violation("R9", "research_isolation", "a.py", "detail"),
            Violation("R11", "dependency_direction", "b.py", "detail"),
        ),
    )
    assert format_summary(pass_report) == "PASS"
    assert "research_isolation=1" in format_summary(fail_report)
    assert "dependency_direction=1" in format_summary(fail_report)
