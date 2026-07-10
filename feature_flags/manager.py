"""Runtime feature flag manager."""

from __future__ import annotations

from feature_flags.defaults import FeatureFlagDefaults, FeatureFlagName
from feature_flags.providers import (
    DefaultsFeatureFlagProvider,
    EnvironmentFeatureFlagProvider,
    FeatureFlagProvider,
    YamlFeatureFlagProvider,
)


class FeatureFlagManager:
    """Resolves feature flags from defaults, YAML, and environment overrides."""

    def __init__(self, providers: tuple[FeatureFlagProvider, ...] | None = None) -> None:
        self._providers = providers or (
            DefaultsFeatureFlagProvider(),
            YamlFeatureFlagProvider(),
            EnvironmentFeatureFlagProvider(),
        )
        self._cache: dict[str, bool] | None = None

    def refresh(self) -> dict[str, bool]:
        """Reload flags from all providers. Later providers override earlier ones."""
        resolved = FeatureFlagDefaults().as_dict()
        for provider in self._providers:
            resolved.update(provider.resolve())
        self._cache = resolved
        return dict(resolved)

    def all_flags(self) -> dict[str, bool]:
        if self._cache is None:
            return self.refresh()
        return dict(self._cache)

    def is_enabled(self, flag: FeatureFlagName | str) -> bool:
        name = flag.value if isinstance(flag, FeatureFlagName) else flag
        flags = self.all_flags()
        if name not in flags:
            msg = f"Unknown feature flag: {name}"
            raise KeyError(msg)
        return flags[name]

    def require_enabled(self, flag: FeatureFlagName) -> None:
        if not self.is_enabled(flag):
            msg = f"Feature flag must be enabled: {flag.value}"
            raise PermissionError(msg)


_manager: FeatureFlagManager | None = None


def get_feature_flag_manager() -> FeatureFlagManager:
    global _manager
    if _manager is None:
        _manager = FeatureFlagManager()
        _manager.refresh()
    return _manager


def reset_feature_flag_manager() -> None:
    global _manager
    _manager = None
