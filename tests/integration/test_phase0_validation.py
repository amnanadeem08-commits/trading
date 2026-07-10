"""Integration tests for Phase 0 validation scripts."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _run_script(script_name: str) -> int:
    completed = subprocess.run(
        [sys.executable, f"scripts/{script_name}"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode


@pytest.mark.integration
def test_validate_environment_passes() -> None:
    assert _run_script("validate_environment.py") == 0


@pytest.mark.integration
def test_validate_configuration_passes() -> None:
    assert _run_script("validate_configuration.py") == 0


@pytest.mark.integration
def test_validate_dependencies_passes() -> None:
    assert _run_script("validate_dependencies.py") == 0


@pytest.mark.integration
def test_validate_architecture_passes() -> None:
    assert _run_script("validate_architecture.py") == 0


@pytest.mark.integration
def test_validate_release_passes() -> None:
    assert _run_script("validate_release.py") == 0
