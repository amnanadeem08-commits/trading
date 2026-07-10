"""Shared fixtures for architecture validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from architecture.validators import ArchitectureReport, ArchitectureValidator

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def validator() -> ArchitectureValidator:
    return ArchitectureValidator(PROJECT_ROOT)


@pytest.fixture
def architecture_report(validator: ArchitectureValidator) -> ArchitectureReport:
    return validator.validate_all()
