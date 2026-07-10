#!/usr/bin/env python3
"""Phase 0 foundation gate validation and certification generator."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class GateCheck:
    category: str
    name: str
    passed: bool
    detail: str


def _run_phase0_checks(project_root: Path) -> list[GateCheck]:
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from architecture.validators import ArchitectureValidator
    from scripts.validation_core import (
        FOUNDATION_PACKAGES,
        LINT_TARGETS,
        REQUIRED_DOCKER,
        REQUIRED_DOCS,
        REQUIRED_SCRIPTS,
        CheckResult,
        check_files_exist,
        python_executable,
        run_command,
        scan_for_todos,
    )

    checks: list[GateCheck] = []

    def add(category: str, result: CheckResult) -> None:
        checks.append(GateCheck(category, result.name, result.passed, result.detail))

    code, output = run_command(
        [python_executable(), "-m", "ruff", "check", *LINT_TARGETS],
        cwd=project_root,
    )
    add(
        "quality",
        CheckResult("ruff", code == 0, "Ruff lint passed" if code == 0 else "Ruff failed", output),
    )

    code, output = run_command(
        [python_executable(), "-m", "black", "--check", *LINT_TARGETS],
        cwd=project_root,
    )
    add(
        "quality",
        CheckResult(
            "black", code == 0, "Black format passed" if code == 0 else "Black failed", output
        ),
    )

    code, output = run_command(
        [python_executable(), "-m", "mypy", *FOUNDATION_PACKAGES],
        cwd=project_root,
    )
    add(
        "quality",
        CheckResult(
            "mypy", code == 0, "Mypy strict passed" if code == 0 else "Mypy failed", output
        ),
    )

    arch_report = ArchitectureValidator(project_root).validate_all()
    add(
        "architecture",
        CheckResult(
            "architecture_validator",
            not arch_report.violations,
            f"Scanned {arch_report.files_scanned} files, {len(arch_report.violations)} violations",
        ),
    )

    code, output = run_command(
        [
            python_executable(),
            "-c",
            "from importlinter.cli import lint_imports_command; lint_imports_command()",
        ],
        cwd=project_root,
    )
    add(
        "architecture",
        CheckResult(
            "import_linter",
            code == 0,
            "Import-linter contracts kept" if code == 0 else "Import-linter failed",
            output,
        ),
    )

    cov_args = [f"--cov={package}" for package in FOUNDATION_PACKAGES]
    code, output = run_command(
        [
            python_executable(),
            "-m",
            "pytest",
            "tests/unit",
            "tests/contract",
            "tests/architecture",
            "tests/integration",
            "-q",
            "--cov-fail-under=88",
            *cov_args,
            "--cov-report=term-missing:skip-covered",
        ],
        cwd=project_root,
    )
    add(
        "tests",
        CheckResult(
            "pytest_coverage",
            code == 0,
            "Pytest passed with coverage >= 88%" if code == 0 else "Tests or coverage failed",
            output,
        ),
    )

    for script_name, script_path in (
        ("environment", "scripts/validate_environment.py"),
        ("configuration", "scripts/validate_configuration.py"),
        ("dependencies", "scripts/validate_dependencies.py"),
        ("release", "scripts/validate_release.py"),
    ):
        code, output = run_command([python_executable(), script_path], cwd=project_root)
        add(
            "validation",
            CheckResult(
                script_name,
                code == 0,
                (
                    f"{script_name} validation passed"
                    if code == 0
                    else f"{script_name} validation failed"
                ),
                output,
            ),
        )

    doc_result = check_files_exist(REQUIRED_DOCS)
    add("documentation", doc_result)

    script_result = check_files_exist(REQUIRED_SCRIPTS)
    add("foundation", CheckResult("scripts", script_result.passed, script_result.detail))

    docker_result = check_files_exist(REQUIRED_DOCKER)
    add("foundation", CheckResult("docker", docker_result.passed, docker_result.detail))

    todos = scan_for_todos()
    add(
        "foundation",
        CheckResult(
            "no_todos",
            not todos,
            (
                "No developer marker comments in foundation code"
                if not todos
                else f"Found {len(todos)} markers"
            ),
        ),
    )

    foundation_packages = [
        "models",
        "config",
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
    ]
    missing_packages = [name for name in foundation_packages if not (project_root / name).is_dir()]
    add(
        "foundation",
        CheckResult(
            "packages",
            not missing_packages,
            (
                "All foundation packages present"
                if not missing_packages
                else f"Missing: {', '.join(missing_packages)}"
            ),
        ),
    )

    return checks


def _render_certification(checks: list[GateCheck], *, generated_at: datetime) -> str:
    passed = sum(1 for check in checks if check.passed)
    total = len(checks)
    gate_passed = passed == total
    status = "CERTIFIED" if gate_passed else "NOT CERTIFIED"

    lines = [
        "# Phase 0 Certification Report",
        "",
        f"**Status:** {status}",
        f"**Generated:** {generated_at.isoformat()}",
        f"**Checks:** {passed}/{total} passed",
        "",
        "## Architecture Freeze v1.0",
        "",
        "The following packages are frozen. Changes require an Architecture Change Proposal (ACP):",
        "",
        "- `models/`",
        "- `config/`",
        "- `events/`",
        "- `versioning/`",
        "- `audit/`",
        "- `feature_flags/`",
        "- `connectors/base.py`",
        "",
        "Breaking changes must increment schema/version and include a migration path.",
        "",
        "## Gate Results",
        "",
        "| Category | Check | Status | Detail |",
        "|---|---|---|---|",
    ]
    for check in checks:
        status_icon = "PASS" if check.passed else "FAIL"
        lines.append(f"| {check.category} | {check.name} | {status_icon} | {check.detail} |")

    lines.extend(
        [
            "",
            "## Foundation Coverage",
            "",
            "| Area | Status |",
            "|---|---|",
            "| Models & Config | Included |",
            "| Connector Foundation | Included |",
            "| Governance (events, versioning, audit, feature_flags, research) | Included |",
            "| Architecture Enforcement | Included |",
            "| Operational (health, metrics, logging, security, notifications, monitoring) | Included |",
            "",
            "## Phase 0 Gate Criteria",
            "",
            "- Architecture validation",
            "- Import-linter",
            "- mypy strict",
            "- Ruff",
            "- Black",
            "- Pytest",
            "- Coverage >= 88%",
            "- Configuration validation",
            "- Environment validation",
            "- Documentation exists",
            "- No developer marker comments",
            "- No dependency violations",
            "",
            "## Recommendation",
            "",
        ]
    )
    if gate_passed:
        lines.append("**Approved to proceed to Phase 1** pending explicit authorization.")
    else:
        lines.append("**Do not proceed to Phase 1.** Resolve failing checks first.")

    return "\n".join(lines) + "\n"


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    checks = _run_phase0_checks(project_root)
    generated_at = datetime.now(UTC)
    report = _render_certification(checks, generated_at=generated_at)

    output_path = project_root / "PHASE0_CERTIFICATION.md"
    output_path.write_text(report, encoding="utf-8")

    print("Phase 0 Foundation Gate")
    print("=====================")
    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.category}/{check.name}: {check.detail}")
    print("")
    print(f"Certification written to {output_path}")
    failed = [check for check in checks if not check.passed]
    print(
        f"Summary: {'CERTIFIED' if not failed else 'NOT CERTIFIED'} ({len(checks) - len(failed)}/{len(checks)})"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
