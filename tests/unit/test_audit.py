"""Unit tests for audit scaffolds."""

from __future__ import annotations

import json

import pytest

from audit import AuditExporter, AuditLogger, AuditReader, AuditReplayer, InMemoryAuditStore
from models.common import ReproducibilityKey
from models.decision import DecisionState
from models.events import AuditRecord
from models.risk import RiskVerdictStatus


def _audit_record(event_id: str = "evt-1") -> AuditRecord:
    return AuditRecord(
        event_id=event_id,
        market_id="crypto:binance",
        symbol_id="BTC/USDT",
        connector_version="0.1.0",
        strategy_version="1.0.0",
        model_version="ml-1",
        prompt_version="prompt-1",
        feature_snapshot_version="fs-1",
        confidence=0.5,
        decision=DecisionState.HOLD,
        risk_verdict=RiskVerdictStatus.APPROVED,
        reproducibility=ReproducibilityKey(
            feature_snapshot_version="fs-1",
            model_version="ml-1",
            prompt_version="prompt-1",
            strategy_version="strategy-1",
            schema_version="1.0.0",
            config_hash="hash-1",
        ),
        feature_flags_active={"SIGNAL_ONLY": True},
    )


@pytest.mark.unit
def test_audit_write_read_append_only() -> None:
    store = InMemoryAuditStore()
    logger = AuditLogger(store)
    reader = AuditReader(store)

    record = _audit_record()
    logger.write(record)
    records = reader.read(market_id="crypto:binance")

    assert len(records) == 1
    assert records[0].audit_id == record.audit_id


@pytest.mark.unit
def test_audit_export_json() -> None:
    store = InMemoryAuditStore()
    logger = AuditLogger(store)
    exporter = AuditExporter(store)

    logger.write(_audit_record())
    exported = exporter.export_json(market_id="crypto:binance")
    payload = json.loads(exported)

    assert len(payload) == 1
    assert payload[0]["market_id"] == "crypto:binance"


@pytest.mark.unit
def test_audit_replay() -> None:
    store = InMemoryAuditStore()
    logger = AuditLogger(store)
    replayer = AuditReplayer(store)
    logger.write(_audit_record())

    replayed: list[str] = []
    count = replayer.replay(lambda record: replayed.append(record.event_id))

    assert count == 1
    assert replayed == ["evt-1"]
