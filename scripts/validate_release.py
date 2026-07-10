#!/usr/bin/env python3
"""Validate release readiness for the platform package."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from scripts.validation_core import (
        PROJECT_ROOT,
        REQUIRED_DOCKER,
        REQUIRED_DOCS,
        REQUIRED_SCRIPTS,
        CheckResult,
        scan_for_todos,
    )

    results: list[CheckResult] = []

    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version_match = re.search(r'^version = "([^"]+)"', pyproject_text, re.MULTILINE)
    version = version_match.group(1) if version_match else ""
    semver_ok = bool(re.fullmatch(r"\d+\.\d+\.\d+", version))
    results.append(
        CheckResult(
            "semver",
            semver_ok,
            f"Release version {version}" if semver_ok else "Invalid semver in pyproject.toml",
        )
    )

    readme_ok = (PROJECT_ROOT / "README.md").is_file()
    results.append(
        CheckResult("readme", readme_ok, "README.md present" if readme_ok else "Missing README.md")
    )

    changelog_note = (PROJECT_ROOT / "docs" / "development" / "release_process.md").is_file()
    results.append(
        CheckResult(
            "release_docs",
            changelog_note,
            "Release process documented" if changelog_note else "Missing release_process.md",
        )
    )

    missing_scripts = [path for path in REQUIRED_SCRIPTS if not (PROJECT_ROOT / path).is_file()]
    results.append(
        CheckResult(
            "release_scripts",
            not missing_scripts,
            (
                "All validation scripts present"
                if not missing_scripts
                else f"Missing: {', '.join(missing_scripts)}"
            ),
        )
    )

    missing_docs = [path for path in REQUIRED_DOCS if not (PROJECT_ROOT / path).is_file()]
    results.append(
        CheckResult(
            "release_docs_complete",
            not missing_docs,
            (
                "All required documentation present"
                if not missing_docs
                else f"Missing: {', '.join(missing_docs)}"
            ),
        )
    )

    missing_docker = [path for path in REQUIRED_DOCKER if not (PROJECT_ROOT / path).is_file()]
    results.append(
        CheckResult(
            "docker_scaffolds",
            not missing_docker,
            (
                "Docker scaffolds present"
                if not missing_docker
                else f"Missing: {', '.join(missing_docker)}"
            ),
        )
    )

    todos = scan_for_todos()
    results.append(
        CheckResult(
            "no_todos",
            not todos,
            "No TODO markers in foundation code" if not todos else f"Found: {', '.join(todos[:5])}",
        )
    )

    print("Release Validation Report")
    print("=========================")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")

    failed = [result for result in results if not result.passed]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
