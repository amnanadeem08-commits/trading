"""Shared validation primitives for Phase 0 gate checks."""

from __future__ import annotations

import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FOUNDATION_PACKAGES: tuple[str, ...] = (
    "models",
    "config",
    "historical",
    "market_data",
    "feature_engineering",
    "feature_store",
    "training_pipeline",
    "model_registry",
    "inference_pipeline",
    "ml_runtime",
    "ml_engine_plugins",
    "framework_adapters",
    "artifact_management",
    "storage_providers",
    "connectors",
    "events",
    "versioning",
    "audit",
    "feature_flags",
    "research",
    "architecture",
    "health",
    "metrics",
    "platform_logging",
    "security",
    "notifications",
    "monitoring",
    "services",
    "pipeline",
    "workflow",
    "data",
    "core",
    "ml",
    "ai",
    "decision",
    "risk",
    "execution",
    "plugins",
)

LINT_TARGETS: tuple[str, ...] = (*FOUNDATION_PACKAGES, "scripts", "tests")

REQUIRED_DOCS: tuple[str, ...] = (
    "docs/setup.md",
    "docs/project_structure.md",
    "docs/configuration.md",
    "docs/phase_gate.md",
    "docs/development/testing.md",
    "docs/development/release_process.md",
    "docs/architecture/foundation_summary.md",
    "docs/architecture/foundation_freeze.md",
    "docs/architecture/phase-0.md",
    "docs/architecture/enforcement.md",
    "docs/architecture/governance_architecture.md",
    "docs/architecture/connector_architecture.md",
)

REQUIRED_SCRIPTS: tuple[str, ...] = (
    "scripts/bootstrap.py",
    "scripts/dev.py",
    "scripts/release.py",
    "scripts/validate_architecture.py",
    "scripts/validate_environment.py",
    "scripts/validate_configuration.py",
    "scripts/validate_dependencies.py",
    "scripts/validate_release.py",
    "scripts/validate_phase0.py",
    "scripts/foundation_certification.py",
)

REQUIRED_DOCKER: tuple[str, ...] = (
    "Dockerfile",
    "Dockerfile.dev",
    "docker-compose.dev.yml",
    "docker-compose.test.yml",
)

REQUIRED_ENV_EXAMPLE_KEYS: tuple[str, ...] = (
    "ENVIRONMENT",
    "APP_NAME",
    "SCHEMA_VERSION",
    "TIMEZONE_INTERNAL",
)

TODO_PATTERN = re.compile(
    r"^\s*#.*\b(TODO|FIXME|HACK|PLACEHOLDER)\b",
    re.IGNORECASE,
)

SCAN_EXCLUDE_PREFIXES: tuple[str, ...] = (
    "core/indicators.py",
    "core/sentiment.py",
    "core/llm_analyzer.py",
    "core/signal_universe.py",
    "connectors/binance_connector.py",
    "connectors/psx_connector.py",
    "connectors/pmex_connector.py",
    "main.py",
    "dashboard.py",
    "legacy_config.py",
    "tests/test_llm_analyzer.py",
    "tests/test_signal_universe.py",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str
    output: str = ""


def run_command(command: list[str], *, cwd: Path | None = None) -> tuple[int, str]:
    """Run a command and return exit code and combined output."""
    completed = subprocess.run(
        command,
        cwd=cwd or PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode, output


def python_executable() -> str:
    return sys.executable


def scan_for_todos() -> list[str]:
    """Scan foundation packages for TODO/FIXME/PLACEHOLDER/HACK markers."""
    violations: list[str] = []
    for package in FOUNDATION_PACKAGES:
        package_dir = PROJECT_ROOT / package
        if not package_dir.exists():
            continue
        for path in package_dir.rglob("*.py"):
            relative = path.relative_to(PROJECT_ROOT).as_posix()
            if any(relative.startswith(prefix) for prefix in SCAN_EXCLUDE_PREFIXES):
                continue
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if TODO_PATTERN.search(line):
                    violations.append(f"{relative}:{line_number}")
    scripts_dir = PROJECT_ROOT / "scripts"
    for path in scripts_dir.rglob("*.py"):
        relative = path.relative_to(PROJECT_ROOT).as_posix()
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if TODO_PATTERN.search(line):
                violations.append(f"{relative}:{line_number}")
    return violations


def check_files_exist(paths: tuple[str, ...]) -> CheckResult:
    missing = [path for path in paths if not (PROJECT_ROOT / path).is_file()]
    if missing:
        return CheckResult("documentation", False, f"Missing files: {', '.join(missing)}")
    return CheckResult("documentation", True, f"All {len(paths)} required files exist")


def run_check(name: str, runner: Callable[[], CheckResult]) -> CheckResult:
    try:
        return runner()
    except Exception as error:
        return CheckResult(name, False, f"Check failed with error: {error}")
