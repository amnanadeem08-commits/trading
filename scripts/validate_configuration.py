#!/usr/bin/env python3
"""Validate platform configuration sources and hash generation."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from config.hash import (
        compute_configuration_hash,
        configuration_files_exist,
        list_configuration_files,
    )
    from config.settings import AppSettings, reset_settings
    from scripts.validation_core import CheckResult

    results: list[CheckResult] = []

    files_ok = configuration_files_exist()
    results.append(
        CheckResult(
            "config_files",
            files_ok,
            (
                "All YAML configuration files present"
                if files_ok
                else "Missing one or more YAML configuration files"
            ),
        )
    )

    settings = None
    try:
        reset_settings()
        settings = AppSettings.from_sources()
        results.append(
            CheckResult(
                "settings_load",
                True,
                f"Loaded settings for {settings.app_name} ({settings.environment})",
            )
        )
    except Exception as error:
        results.append(CheckResult("settings_load", False, str(error)))

    try:
        config_hash = compute_configuration_hash()
        valid_hash = len(config_hash) == 64 and all(
            char in "0123456789abcdef" for char in config_hash
        )
        results.append(
            CheckResult(
                "config_hash",
                valid_hash,
                f"Configuration hash: {config_hash[:16]}... ({len(list_configuration_files())} files)",
            )
        )
    except Exception as error:
        results.append(CheckResult("config_hash", False, str(error)))

    if settings is not None:
        if settings.feature_flags.live_trading_enabled:
            results.append(
                CheckResult("safe_defaults", False, "live_trading_enabled must be false")
            )
        elif settings.feature_flags.signal_only:
            results.append(
                CheckResult("safe_defaults", True, "Production-safe feature flag defaults")
            )
        else:
            results.append(CheckResult("safe_defaults", False, "signal_only must be true"))
    else:
        results.append(
            CheckResult("safe_defaults", False, "Cannot verify defaults without loaded settings")
        )

    print("Configuration Validation Report")
    print("===============================")
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.detail}")

    failed = [result for result in results if not result.passed]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
