"""Market data bridge for feature engineering."""

from __future__ import annotations

from feature_engineering.extraction.extraction_context import FeatureExtractionContext
from feature_engineering.extraction.extraction_pipeline import FeatureExtractionPipeline
from feature_engineering.extraction.extraction_result import FeatureExtractionResult
from feature_engineering.models.feature_batch import FeatureBatch
from feature_engineering.models.feature_set import FeatureSet
from feature_engineering.registry.feature_catalog import FeatureCatalogEntry
from feature_engineering.registry.feature_registry import FeatureRegistry
from feature_engineering.schema.feature_schema import FeatureSchema
from feature_engineering.schema.schema_registry import FeatureSchemaRegistry
from feature_engineering.versioning.feature_version import FeatureVersion, FeatureVersionRegistry
from market_data.stream.stream_buffer import StreamBuffer


def build_pipeline_from_stream(
    stream_buffer: StreamBuffer,
    *,
    pipeline_id: str = "feature-pipeline",
    schema_id: str = "feature-schema-v1",
    batch_size: int = 10,
    window_size: int = 1,
) -> FeatureExtractionPipeline:
    """Build a feature extraction pipeline from a market data stream."""
    context = stream_buffer.context
    extraction_context = FeatureExtractionContext(
        pipeline_id=pipeline_id,
        dataset_id=context.dataset_id,
        symbol_id=context.symbol_id,
        schema_id=schema_id,
        batch_size=batch_size,
        window_size=window_size,
        correlation_id=context.correlation_id,
        trace_id=context.trace_id,
    )
    return FeatureExtractionPipeline(extraction_context, stream_buffer=stream_buffer)


def extract_batch_from_stream(
    stream_buffer: StreamBuffer,
    *,
    pipeline_id: str = "feature-pipeline",
    page: int = 0,
) -> FeatureBatch:
    """Extract a feature batch from a market data stream."""
    pipeline = build_pipeline_from_stream(stream_buffer, pipeline_id=pipeline_id)
    return pipeline.extract_batch(page=page)


def extract_set_from_stream(
    stream_buffer: StreamBuffer,
    *,
    pipeline_id: str = "feature-pipeline",
    page: int = 0,
) -> FeatureSet:
    """Extract a feature set from a market data stream."""
    pipeline = build_pipeline_from_stream(stream_buffer, pipeline_id=pipeline_id)
    return pipeline.extract_set(page=page)


def run_extraction_from_stream(
    stream_buffer: StreamBuffer,
    *,
    pipeline_id: str = "feature-pipeline",
    max_batches: int = 1,
) -> FeatureExtractionResult:
    """Run feature extraction from a market data stream."""
    pipeline = build_pipeline_from_stream(stream_buffer, pipeline_id=pipeline_id)
    return pipeline.run(max_batches=max_batches)


def register_feature_from_schema(
    schema_registry: FeatureSchemaRegistry,
    feature_registry: FeatureRegistry,
    *,
    schema: FeatureSchema,
    feature_id: str,
    dataset_id: str,
    symbol_id: str,
    capabilities: tuple[str, ...] = ("extract", "validate"),
) -> FeatureCatalogEntry:
    """Register a feature catalog entry from a schema definition."""
    schema_registry.register(schema)
    entry = FeatureCatalogEntry(
        feature_id=feature_id,
        name=schema.name,
        schema_id=schema.schema_id,
        version=schema.version,
        dataset_id=dataset_id,
        symbol_id=symbol_id,
        capabilities=capabilities,
        tags=("feature",),
    )
    feature_registry.register(entry)
    return entry


def register_version_from_schema(
    schema: FeatureSchema,
    version_registry: FeatureVersionRegistry,
    *,
    feature_id: str,
    snapshot_id: str,
) -> FeatureVersion:
    """Register version metadata from a feature schema."""
    version = FeatureVersion(
        feature_id=feature_id,
        version=schema.version,
        schema_id=schema.schema_id,
        description=schema.description,
        snapshot_id=snapshot_id,
    )
    version_registry.register(version)
    return version
