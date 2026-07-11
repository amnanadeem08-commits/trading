"""Unit tests for market/feature intake mappers."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from feature_engineering.models.feature import Feature
from feature_engineering.models.feature_metadata import FeatureMetadata
from feature_engineering.models.feature_set import FeatureSet
from feature_engineering.models.feature_vector import FeatureVector
from feature_store.models.feature_record import FeatureRecord
from feature_store.models.feature_snapshot import FeatureSnapshot
from market_data.models.candle import Candle
from market_data.models.market_record import MarketRecord, MarketRecordType
from models.common import ReproducibilityKey
from models.decision import DecisionSource, DecisionState
from models.signal import InvalidationRule
from signal_engine import (
    SignalAssembler,
    SignalAssemblyRequest,
    SignalIntakeError,
    feature_intake_from_set,
    feature_intake_from_store_record,
    feature_intake_from_vector,
    market_intake_from_candle,
    market_intake_from_record,
    provenance_from_intake,
    snapshot_ref_from_snapshot,
)
from tests.signal_helpers import make_risk_assessment


def _candle() -> Candle:
    return Candle(
        record_id="c-1",
        dataset_id="crypto:binance",
        symbol_id="BTC/USDT",
        timestamp=datetime(2026, 7, 11, tzinfo=UTC),
        open=100.0,
        high=110.0,
        low=95.0,
        close=105.0,
        volume=12.5,
        sequence=1,
    )


def _vector() -> FeatureVector:
    return FeatureVector(
        vector_id="v-1",
        dataset_id="crypto:binance",
        symbol_id="BTC/USDT",
        record_id="c-1",
        features=(
            Feature(name="rsi_14", value=58.0),
            Feature(name="macd", value=0.12),
        ),
        timestamp=datetime(2026, 7, 11, tzinfo=UTC),
        version="fs-1",
    )


@pytest.mark.unit
def test_market_intake_from_candle_and_record() -> None:
    frame = market_intake_from_candle(_candle(), market_id="crypto:binance")
    assert frame.market_id == "crypto:binance"
    assert frame.ohlcv["close"] == 105.0
    record = MarketRecord(
        record_id="r-1",
        dataset_id="crypto:binance",
        symbol_id="BTC/USDT",
        record_type=MarketRecordType.CANDLE,
        attributes={"open": "1", "close": "2", "volume": "3"},
    )
    mapped = market_intake_from_record(record, market_id="crypto:binance")
    assert mapped.ohlcv["close"] == 2.0
    assert mapped.raw_attributes["open"] == "1"


@pytest.mark.unit
def test_market_intake_rejects_bad_ohlcv() -> None:
    record = MarketRecord(
        record_id="r-bad",
        dataset_id="crypto:binance",
        symbol_id="BTC/USDT",
        record_type=MarketRecordType.CANDLE,
        attributes={"close": "not-a-number"},
    )
    with pytest.raises(SignalIntakeError, match="Invalid OHLCV"):
        market_intake_from_record(record)


@pytest.mark.unit
def test_feature_intake_from_vector_set_and_store() -> None:
    payload = feature_intake_from_vector(_vector())
    assert payload.indicators_used == ("rsi_14", "macd")
    assert payload.indicator_values["rsi_14"] == 58.0

    feature_set = FeatureSet(
        feature_set_id="set-1",
        vectors=(_vector(),),
        metadata=FeatureMetadata(
            feature_set_id="set-1",
            dataset_id="crypto:binance",
            symbol_id="BTC/USDT",
            schema_id="schema-1",
        ),
    )
    payloads = feature_intake_from_set(feature_set, symbol_id="BTC/USDT")
    assert len(payloads) == 1

    store_record = FeatureRecord(
        record_id="fr-1",
        dataset_id="crypto:binance",
        symbol_id="BTC/USDT",
        vector_id="v-1",
        source_record_id="c-1",
        version="fs-1",
        values={"rsi_14": "58.0", "flag": "true"},
    )
    store_payload = feature_intake_from_store_record(store_record)
    assert store_payload.indicator_values["flag"] is True


@pytest.mark.unit
def test_feature_intake_rejects_empty_and_symbol_miss() -> None:
    with pytest.raises(SignalIntakeError, match="must not be empty"):
        feature_intake_from_vector(
            FeatureVector(
                vector_id="v-empty",
                dataset_id="crypto:binance",
                symbol_id="BTC/USDT",
                record_id="c-1",
                features=(),
            )
        )
    feature_set = FeatureSet(
        feature_set_id="set-1",
        vectors=(_vector(),),
        metadata=FeatureMetadata(
            feature_set_id="set-1",
            dataset_id="crypto:binance",
            symbol_id="BTC/USDT",
            schema_id="schema-1",
        ),
    )
    with pytest.raises(SignalIntakeError, match="No feature vectors matched"):
        feature_intake_from_set(feature_set, symbol_id="ETH/USDT")


@pytest.mark.unit
def test_snapshot_and_provenance_feed_assembler() -> None:
    market = market_intake_from_candle(_candle(), market_id="crypto:binance")
    features = feature_intake_from_vector(_vector())
    snapshot = snapshot_ref_from_snapshot(
        FeatureSnapshot(
            snapshot_id="snap-1",
            dataset_id="crypto:binance",
            version="fs-snap-1",
            checksum="abc",
            lineage=("v-1",),
        )
    )
    provenance = provenance_from_intake(
        market=market,
        features=features,
        snapshot=snapshot,
        connector_version="md-1.0.0",
        prompt_version="prompt-1",
        strategy_version="strategy-1",
    )
    assert provenance.market_id == "crypto:binance"
    assert provenance.feature_snapshot_version == "fs-snap-1"

    request = SignalAssemblyRequest(
        signal_id="sig-intake-1",
        symbol_id=features.symbol_id,
        market_id=market.market_id,
        decision=DecisionState.HOLD,
        decision_source=DecisionSource.STATISTICAL_ONLY,
        indicators_used=features.indicators_used,
        indicator_values=features.indicator_values,
        confidence=0.5,
        risk_assessment=make_risk_assessment(),
        invalidation=InvalidationRule(condition="Break below support"),
        alternative_scenario="Breakout would shift bias to BUY.",
        provenance=provenance,
        reproducibility=ReproducibilityKey(
            feature_snapshot_version=provenance.feature_snapshot_version,
            model_version="ml-1",
            prompt_version="prompt-1",
            strategy_version="strategy-1",
            schema_version="1.0.0",
            config_hash="abc123",
        ),
    )
    signal = SignalAssembler().assemble(request)
    assert signal.provenance.feature_snapshot_version == "fs-snap-1"
    assert signal.indicators_used == ("rsi_14", "macd")


@pytest.mark.unit
def test_provenance_requires_matching_symbols() -> None:
    market = market_intake_from_candle(_candle(), market_id="crypto:binance")
    features = feature_intake_from_vector(
        FeatureVector(
            vector_id="v-2",
            dataset_id="crypto:binance",
            symbol_id="ETH/USDT",
            record_id="c-2",
            features=(Feature(name="rsi_14", value=40.0),),
            version="fs-1",
        )
    )
    with pytest.raises(SignalIntakeError, match="symbol_id must match"):
        provenance_from_intake(market=market, features=features)
