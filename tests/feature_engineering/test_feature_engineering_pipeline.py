"""Unit tests for feature extraction pipeline."""

from __future__ import annotations

import pytest

from feature_engineering import AttributeFeatureExtractor, FeatureExtractionPipeline
from tests.feature_engineering_helpers import (
    make_extraction_context,
    make_sample_candle,
    make_stream_buffer_from_candles,
)


@pytest.mark.unit
def test_extract_vector_from_candle_record() -> None:
    context = make_extraction_context()
    pipeline = FeatureExtractionPipeline(context)
    record = make_sample_candle(close=105.0).to_market_record()
    vector = pipeline.extract_vector(record)
    names = {feature.name for feature in vector.features}
    assert "close" in names
    assert vector.record_id == record.record_id


@pytest.mark.unit
def test_extract_batch_from_records() -> None:
    context = make_extraction_context(batch_size=2)
    records = tuple(
        make_sample_candle(record_id=f"record-{index}", sequence=index).to_market_record()
        for index in range(3)
    )
    pipeline = FeatureExtractionPipeline(context, records=records)
    batch = pipeline.extract_batch(page=0)
    assert len(batch.vectors) == 2
    assert batch.offset == 0


@pytest.mark.unit
def test_extract_batch_from_stream() -> None:
    context = make_extraction_context(batch_size=2)
    stream = make_stream_buffer_from_candles(record_count=3)
    pipeline = FeatureExtractionPipeline(context, stream_buffer=stream)
    batch = pipeline.extract_batch(page=0)
    assert len(batch.vectors) == 2


@pytest.mark.unit
def test_extract_set_produces_metadata() -> None:
    context = make_extraction_context()
    stream = make_stream_buffer_from_candles(record_count=2)
    pipeline = FeatureExtractionPipeline(context, stream_buffer=stream)
    feature_set = pipeline.extract_set(page=0)
    assert feature_set.metadata.record_count == 2
    assert feature_set.metadata.extractor_id == "attribute-extractor"


@pytest.mark.unit
def test_extract_window() -> None:
    context = make_extraction_context()
    records = tuple(
        make_sample_candle(record_id=f"record-{index}", sequence=index).to_market_record()
        for index in range(3)
    )
    pipeline = FeatureExtractionPipeline(context, records=records)
    window = pipeline.extract_window(size=2)
    assert len(window.vectors) == 2


@pytest.mark.unit
def test_run_extraction() -> None:
    context = make_extraction_context()
    stream = make_stream_buffer_from_candles(record_count=3)
    pipeline = FeatureExtractionPipeline(context, stream_buffer=stream)
    result = pipeline.run(max_batches=2)
    assert result.vectors_extracted >= 2
    assert result.feature_set is not None


@pytest.mark.unit
def test_next_from_stream() -> None:
    context = make_extraction_context()
    stream = make_stream_buffer_from_candles(record_count=1)
    pipeline = FeatureExtractionPipeline(context, stream_buffer=stream)
    vector = pipeline.next_from_stream()
    assert vector is not None
    assert vector.dataset_id == "dataset-1"


@pytest.mark.unit
def test_custom_extractor_id() -> None:
    extractor = AttributeFeatureExtractor(field_names=("close",))
    assert extractor.extractor_id() == "attribute-extractor"
