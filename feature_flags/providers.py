"""Feature flag configuration providers."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod

from config.loader import load_yaml_config
from feature_flags.defaults import (
    _FLAG_TO_SETTING_KEY,
    FeatureFlagDefaults,
    FeatureFlagName,
)


class FeatureFlagProvider(ABC):
    """Source of feature flag values."""

    @abstractmethod
    def resolve(self) -> dict[str, bool]:
        """Return feature flag values keyed by canonical flag name."""


class DefaultsFeatureFlagProvider(FeatureFlagProvider):
    """Production-safe built-in defaults."""

    def resolve(self) -> dict[str, bool]:
        return FeatureFlagDefaults().as_dict()


class YamlFeatureFlagProvider(FeatureFlagProvider):
    """Load feature flags from config/feature_flags.yaml."""

    def resolve(self) -> dict[str, bool]:
        data = load_yaml_config("feature_flags.yaml")
        section = data.get("feature_flags", {})
        resolved = FeatureFlagDefaults().as_dict()
        for flag in FeatureFlagName:
            key = _FLAG_TO_SETTING_KEY[flag]
            if key in section:
                resolved[flag.value] = bool(section[key])
        return resolved


class EnvironmentFeatureFlagProvider(FeatureFlagProvider):
    """Resolve feature flags from environment variables."""

    _PREFIX = "FEATURE_FLAG_"

    def resolve(self) -> dict[str, bool]:
        resolved: dict[str, bool] = {}
        for flag in FeatureFlagName:
            env_name = f"{self._PREFIX}{flag.value}"
            if env_name in os.environ:
                resolved[flag.value] = os.environ[env_name].strip().lower() in {
                    "1",
                    "true",
                    "yes",
                    "on",
                }
        return resolved
