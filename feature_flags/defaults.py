"""Production-safe feature flag defaults."""

from __future__ import annotations

from enum import StrEnum

from models.common import PlatformModel


class FeatureFlagName(StrEnum):
    """Canonical feature flag identifiers."""

    SIGNAL_ONLY = "SIGNAL_ONLY"
    AI_ENABLED = "AI_ENABLED"
    MULTI_AGENT_ENABLED = "MULTI_AGENT_ENABLED"
    RAG_ENABLED = "RAG_ENABLED"
    MEMORY_ENABLED = "MEMORY_ENABLED"
    NEWS_ENABLED = "NEWS_ENABLED"
    MACRO_ENABLED = "MACRO_ENABLED"
    LIVE_TRADING_ENABLED = "LIVE_TRADING_ENABLED"
    PMEX_ENABLED = "PMEX_ENABLED"
    EXPERIMENTAL_MODE = "EXPERIMENTAL_MODE"


_FLAG_TO_SETTING_KEY: dict[FeatureFlagName, str] = {
    FeatureFlagName.SIGNAL_ONLY: "signal_only",
    FeatureFlagName.AI_ENABLED: "ai_enabled",
    FeatureFlagName.MULTI_AGENT_ENABLED: "multi_agent_enabled",
    FeatureFlagName.RAG_ENABLED: "rag_enabled",
    FeatureFlagName.MEMORY_ENABLED: "memory_enabled",
    FeatureFlagName.NEWS_ENABLED: "news_enabled",
    FeatureFlagName.MACRO_ENABLED: "macro_enabled",
    FeatureFlagName.LIVE_TRADING_ENABLED: "live_trading_enabled",
    FeatureFlagName.PMEX_ENABLED: "pmex_enabled",
    FeatureFlagName.EXPERIMENTAL_MODE: "experimental_mode",
}


class FeatureFlagDefaults(PlatformModel):
    """Safe production defaults per Rule R17."""

    signal_only: bool = True
    ai_enabled: bool = True
    multi_agent_enabled: bool = False
    rag_enabled: bool = False
    memory_enabled: bool = False
    news_enabled: bool = False
    macro_enabled: bool = False
    live_trading_enabled: bool = False
    pmex_enabled: bool = False
    experimental_mode: bool = False

    def as_dict(self) -> dict[str, bool]:
        return {flag.value: self.is_enabled(flag) for flag in FeatureFlagName}

    def is_enabled(self, flag: FeatureFlagName) -> bool:
        key = _FLAG_TO_SETTING_KEY[flag]
        return bool(getattr(self, key))
