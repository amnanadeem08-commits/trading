#!/usr/bin/env python3
"""Validate runtime environment prerequisites."""

from __future__ import annotations

import platform
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from scripts.validation_core import PROJECT_ROOT, REQUIRED_ENV_EXAMPLE_KEYS, CheckResult

    results: list[CheckResult] = []

    version = sys.version_info
    py_ok = version.major == 3 and version.minor >= 14
    results.append(
        CheckResult(
            "python_version",
            py_ok,
            f"Python {version.major}.{version.minor}.{version.micro} "
            f"({'>=3.14 required' if not py_ok else 'ok'})",
        )
    )

    env_example = PROJECT_ROOT / ".env.example"
    if not env_example.is_file():
        results.append(CheckResult("env_example", False, ".env.example is missing"))
    else:
        content = env_example.read_text(encoding="utf-8")
        missing_keys = [key for key in REQUIRED_ENV_EXAMPLE_KEYS if key not in content]
        results.append(
            CheckResult(
                "env_example",
                not missing_keys,
                (
                    "All required keys documented"
                    if not missing_keys
                    else f"Missing keys: {', '.join(missing_keys)}"
                ),
            )
        )

    print("Environment Validation Report")
    print("===========================")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")

    print("")
    print(f"Platform: {platform.platform()}")
    print(f"Project root: {PROJECT_ROOT}")
    failed = [result for result in results if not result.passed]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
