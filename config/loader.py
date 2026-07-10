"""YAML configuration loader with environment override support."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from models.common import ConfigurationError

CONFIG_DIR = Path(__file__).resolve().parent


def load_yaml_config(filename: str) -> dict[str, Any]:
    """Load a YAML configuration file from the config directory."""
    path = CONFIG_DIR / filename
    if not path.exists():
        msg = f"Configuration file not found: {path}"
        raise ConfigurationError(msg)
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if data is None:
        return {}
    if not isinstance(data, dict):
        msg = f"Configuration file must contain a mapping: {path}"
        raise ConfigurationError(msg)
    return data


def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Deep-merge configuration mappings. Later configs override earlier ones."""
    merged: dict[str, Any] = {}
    for config in configs:
        _deep_merge(merged, config)
    return merged


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base
