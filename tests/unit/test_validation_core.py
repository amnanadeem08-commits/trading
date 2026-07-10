"""Unit tests for validation core utilities."""

from __future__ import annotations

import pytest

from scripts.validation_core import (
    PROJECT_ROOT,
    REQUIRED_DOCS,
    check_files_exist,
    scan_for_todos,
)


@pytest.mark.unit
def test_required_docs_exist() -> None:
    result = check_files_exist(REQUIRED_DOCS)
    assert result.passed is True


@pytest.mark.unit
def test_scan_for_todos_in_foundation_is_clean() -> None:
    violations = scan_for_todos()
    assert violations == []


@pytest.mark.unit
def test_project_root_points_to_repository() -> None:
    assert (PROJECT_ROOT / "pyproject.toml").is_file()
    assert (PROJECT_ROOT / "scripts" / "validate_phase0.py").is_file()
