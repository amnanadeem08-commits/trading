"""Contract tests for governance scaffolds."""

from __future__ import annotations

import inspect

import pytest

from audit import AuditLogger, AuditReader, AuditStore
from events import EventBus, EventPersistenceStore
from feature_flags import FeatureFlagName
from research import PromotionGate
from versioning import VersionRegistry


@pytest.mark.contract
def test_event_bus_contract_methods() -> None:
    required = {"publish", "subscribe", "unsubscribe"}
    assert required.issubset(set(dir(EventBus)))


@pytest.mark.contract
def test_event_persistence_append_only_contract() -> None:
    required = {"append", "list_events", "count"}
    for name in required:
        assert hasattr(EventPersistenceStore, name)


@pytest.mark.contract
def test_audit_store_contract_methods() -> None:
    required = {"write", "read", "count"}
    for name in required:
        assert hasattr(AuditStore, name)


@pytest.mark.contract
def test_audit_logger_reader_exporter_exist() -> None:
    assert hasattr(AuditLogger, "write")
    assert hasattr(AuditReader, "read")


@pytest.mark.contract
def test_version_registry_contract() -> None:
    required = {"register", "get", "current", "list_versions", "exists"}
    assert required.issubset(set(dir(VersionRegistry)))


@pytest.mark.contract
def test_feature_flag_names_complete() -> None:
    expected = {
        "SIGNAL_ONLY",
        "AI_ENABLED",
        "MULTI_AGENT_ENABLED",
        "RAG_ENABLED",
        "MEMORY_ENABLED",
        "NEWS_ENABLED",
        "MACRO_ENABLED",
        "LIVE_TRADING_ENABLED",
        "PMEX_ENABLED",
        "EXPERIMENTAL_MODE",
    }
    assert {flag.value for flag in FeatureFlagName} == expected


@pytest.mark.contract
def test_promotion_gate_is_abstract() -> None:
    assert inspect.isabstract(PromotionGate)
    assert "evaluate" in PromotionGate.__abstractmethods__
