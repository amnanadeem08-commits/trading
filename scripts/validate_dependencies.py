#!/usr/bin/env python3
"""Validate project dependencies and development tooling."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from scripts.validation_core import PROJECT_ROOT, CheckResult

    results: list[CheckResult] = []

    pyproject = PROJECT_ROOT / "pyproject.toml"
    requirements = PROJECT_ROOT / "requirements.txt"
    results.append(
        CheckResult(
            "dependency_files",
            pyproject.is_file() and requirements.is_file(),
            "pyproject.toml and requirements.txt present",
        )
    )

    core_deps = ("pydantic", "pydantic-settings", "PyYAML", "python-dotenv")
    pyproject_text = pyproject.read_text(encoding="utf-8")
    missing_core = [dep for dep in core_deps if dep not in pyproject_text]
    results.append(
        CheckResult(
            "core_dependencies",
            not missing_core,
            (
                "Core dependencies declared"
                if not missing_core
                else f"Missing: {', '.join(missing_core)}"
            ),
        )
    )

    dev_tools = ("pytest", "mypy", "ruff", "black", "import-linter")
    missing_dev = [tool for tool in dev_tools if tool not in pyproject_text]
    results.append(
        CheckResult(
            "dev_dependencies",
            not missing_dev,
            (
                "Development tools declared"
                if not missing_dev
                else f"Missing: {', '.join(missing_dev)}"
            ),
        )
    )

    importable_modules = {
        "pydantic": "pydantic",
        "pydantic_settings": "pydantic-settings",
        "yaml": "PyYAML",
        "dotenv": "python-dotenv",
    }
    missing: list[str] = []
    for module_name, package_name in importable_modules.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)
    results.append(
        CheckResult(
            "dependency_imports",
            not missing,
            (
                "Core dependencies importable"
                if not missing
                else f"Missing imports: {', '.join(missing)}"
            ),
        )
    )

    version_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', version_text, re.MULTILINE)
    version_ok = match is not None and len(match.group(1).split(".")) == 3
    results.append(
        CheckResult(
            "version_format",
            version_ok,
            f"Project version: {match.group(1)}" if match else "Invalid or missing version",
        )
    )

    print("Dependency Validation Report")
    print("==========================")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")

    failed = [result for result in results if not result.passed]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
