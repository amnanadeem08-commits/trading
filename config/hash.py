"""Configuration hash generation for ReproducibilityKey."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from config.loader import CONFIG_DIR, load_yaml_config, merge_configs

_CONFIG_FILES: tuple[str, ...] = (
    "indicators.yaml",
    "risk.yaml",
    "execution.yaml",
    "connectors.yaml",
    "paper_adapter.yaml",
    "historical.yaml",
    "feature_flags.yaml",
    "markets.yaml",
    "logging.yaml",
    "monitoring.yaml",
    "services.yaml",
    "pipeline.yaml",
    "workflow.yaml",
    "data.yaml",
    "core.yaml",
    "ml.yaml",
    "ai.yaml",
    "decision.yaml",
    "plugins.yaml",
    "security.yaml",
    "notifications.yaml",
)


def load_merged_configuration() -> dict[str, Any]:
    """Load and merge all platform YAML configuration files."""
    configs = [load_yaml_config(name) for name in _CONFIG_FILES]
    return merge_configs(*configs)


def compute_configuration_hash() -> str:
    """Return a stable SHA-256 hash of the merged platform configuration."""
    merged = load_merged_configuration()
    canonical = json.dumps(merged, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def list_configuration_files() -> tuple[str, ...]:
    """Return configuration file names used for hashing."""
    return _CONFIG_FILES


def configuration_files_exist() -> bool:
    """Return whether all required configuration files exist."""
    return all((CONFIG_DIR / name).is_file() for name in _CONFIG_FILES)
