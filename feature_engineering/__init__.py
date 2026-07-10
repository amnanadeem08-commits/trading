"""Feature engineering framework public API."""

from feature_engineering.exceptions import (
    FeatureEngineeringError,
    FeatureExtractionError,
    FeatureNotFoundError,
    FeatureRegistrationError,
    FeatureSchemaError,
    FeatureValidationError,
    FeatureVersionError,
)
from feature_engineering.extraction.extraction_context import FeatureExtractionContext
from feature_engineering.extraction.extraction_pipeline import FeatureExtractionPipeline
from feature_engineering.extraction.extraction_result import FeatureExtractionResult
from feature_engineering.extraction.extractor import AttributeFeatureExtractor, FeatureExtractor
from feature_engineering.integration.market_data_bridge import (
    build_pipeline_from_stream,
    extract_batch_from_stream,
    extract_set_from_stream,
    register_feature_from_schema,
    register_version_from_schema,
    run_extraction_from_stream,
)
from feature_engineering.lifecycle.feature_lifecycle import (
    FeatureExtractionCompletedEvent,
    FeatureExtractionStartedEvent,
    FeatureLifecycleEvent,
    FeatureLifecycleEventType,
    FeatureLifecycleManager,
    FeatureRegisteredEvent,
    FeatureValidationCompletedEvent,
)
from feature_engineering.models.feature import Feature
from feature_engineering.models.feature_batch import FeatureBatch
from feature_engineering.models.feature_metadata import FeatureMetadata
from feature_engineering.models.feature_set import FeatureSet
from feature_engineering.models.feature_vector import FeatureVector
from feature_engineering.models.feature_window import FeatureWindow
from feature_engineering.registry.feature_catalog import FeatureCatalogEntry
from feature_engineering.registry.feature_registry import (
    FeatureRegistry,
    get_feature_registry,
    reset_feature_registry,
)
from feature_engineering.schema.feature_schema import FeatureSchema
from feature_engineering.schema.schema_registry import FeatureSchemaRegistry
from feature_engineering.schema.schema_validator import FeatureSchemaValidator
from feature_engineering.validation.validation_result import FeatureValidationResult
from feature_engineering.validation.validation_rule import (
    FeatureValidationRule,
    NonEmptyVectorRule,
    RequiredFieldsRule,
)
from feature_engineering.validation.validator import FeatureValidator
from feature_engineering.versioning.feature_version import FeatureVersion, FeatureVersionRegistry

__all__ = [
    "AttributeFeatureExtractor",
    "Feature",
    "FeatureBatch",
    "FeatureCatalogEntry",
    "FeatureEngineeringError",
    "FeatureExtractionCompletedEvent",
    "FeatureExtractionContext",
    "FeatureExtractionError",
    "FeatureExtractionPipeline",
    "FeatureExtractionResult",
    "FeatureExtractionStartedEvent",
    "FeatureExtractor",
    "FeatureLifecycleEvent",
    "FeatureLifecycleEventType",
    "FeatureLifecycleManager",
    "FeatureMetadata",
    "FeatureNotFoundError",
    "FeatureRegisteredEvent",
    "FeatureRegistrationError",
    "FeatureRegistry",
    "FeatureSchema",
    "FeatureSchemaError",
    "FeatureSchemaRegistry",
    "FeatureSchemaValidator",
    "FeatureSet",
    "FeatureValidationCompletedEvent",
    "FeatureValidationError",
    "FeatureValidationResult",
    "FeatureValidationRule",
    "FeatureValidator",
    "FeatureVector",
    "FeatureVersion",
    "FeatureVersionError",
    "FeatureVersionRegistry",
    "FeatureWindow",
    "NonEmptyVectorRule",
    "RequiredFieldsRule",
    "build_pipeline_from_stream",
    "extract_batch_from_stream",
    "extract_set_from_stream",
    "get_feature_registry",
    "register_feature_from_schema",
    "register_version_from_schema",
    "reset_feature_registry",
    "run_extraction_from_stream",
]
