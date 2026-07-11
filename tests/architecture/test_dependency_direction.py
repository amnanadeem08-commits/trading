"""Architecture tests for pipeline dependency direction."""

from __future__ import annotations

import pytest

from architecture.dependency_rules import PIPELINE_PACKAGES, PipelineLayer
from tests.architecture.conftest import PROJECT_ROOT


@pytest.mark.architecture
def test_pipeline_layer_order_is_frozen() -> None:
    assert [layer.name for layer in PipelineLayer] == [
        "HISTORICAL",
        "MARKET_DATA",
        "FEATURE_ENGINEERING",
        "CONNECTORS",
        "DATA",
        "CORE",
        "FEATURE_STORE",
        "TRAINING_PIPELINE",
        "MODEL_REGISTRY",
        "INFERENCE_PIPELINE",
        "ML_RUNTIME",
        "ML_ENGINE_PLUGINS",
        "FRAMEWORK_ADAPTERS",
        "ARTIFACT_MANAGEMENT",
        "STORAGE_PROVIDERS",
        "ML",
        "AI",
        "AGENTS",
        "DECISION",
        "RISK",
        "SIGNAL_ENGINE",
        "EXECUTION",
        "PAPER_TRADING",
    ]
    assert PIPELINE_PACKAGES["feature_store"] == PipelineLayer.FEATURE_STORE
    assert PIPELINE_PACKAGES["training_pipeline"] == PipelineLayer.TRAINING_PIPELINE
    assert PIPELINE_PACKAGES["model_registry"] == PipelineLayer.MODEL_REGISTRY
    assert PIPELINE_PACKAGES["inference_pipeline"] == PipelineLayer.INFERENCE_PIPELINE
    assert PIPELINE_PACKAGES["ml_runtime"] == PipelineLayer.ML_RUNTIME
    assert PIPELINE_PACKAGES["ml_engine_plugins"] == PipelineLayer.ML_ENGINE_PLUGINS
    assert PIPELINE_PACKAGES["framework_adapters"] == PipelineLayer.FRAMEWORK_ADAPTERS
    assert PIPELINE_PACKAGES["artifact_management"] == PipelineLayer.ARTIFACT_MANAGEMENT
    assert PIPELINE_PACKAGES["storage_providers"] == PipelineLayer.STORAGE_PROVIDERS
    assert PIPELINE_PACKAGES["ml"] == PipelineLayer.ML
    assert PIPELINE_PACKAGES["signal_engine"] == PipelineLayer.SIGNAL_ENGINE
    assert PIPELINE_PACKAGES["paper_trading"] == PipelineLayer.PAPER_TRADING


@pytest.mark.architecture
def test_no_reverse_pipeline_imports(architecture_report) -> None:
    violations = [
        violation
        for violation in architecture_report.violations
        if violation.rule_name == "dependency_direction"
    ]
    assert violations == []


@pytest.mark.architecture
def test_foundation_packages_do_not_import_pipeline_layers(validator) -> None:
    source_files = validator._load_source_files()
    violations = validator._validate_dependency_direction(source_files)
    foundation_violations = [
        violation for violation in violations if violation.file_path.startswith("models/")
    ]
    assert foundation_violations == []


@pytest.mark.architecture
def test_historical_remains_lowest_pipeline_layer() -> None:
    historical_layer = PIPELINE_PACKAGES["historical"]
    for package, layer in PIPELINE_PACKAGES.items():
        if package == "historical":
            continue
        assert layer > historical_layer


@pytest.mark.architecture
def test_market_data_sits_between_historical_and_feature_engineering() -> None:
    historical_layer = PIPELINE_PACKAGES["historical"]
    market_data_layer = PIPELINE_PACKAGES["market_data"]
    feature_layer = PIPELINE_PACKAGES["feature_engineering"]
    assert market_data_layer > historical_layer
    assert feature_layer > market_data_layer


@pytest.mark.architecture
def test_feature_store_sits_between_core_and_ml() -> None:
    core_layer = PIPELINE_PACKAGES["core"]
    store_layer = PIPELINE_PACKAGES["feature_store"]
    ml_layer = PIPELINE_PACKAGES["ml"]
    assert store_layer > core_layer
    assert ml_layer > store_layer


@pytest.mark.architecture
def test_artifact_management_sits_between_framework_adapters_and_storage_providers() -> None:
    adapters_layer = PIPELINE_PACKAGES["framework_adapters"]
    artifacts_layer = PIPELINE_PACKAGES["artifact_management"]
    storage_layer = PIPELINE_PACKAGES["storage_providers"]
    assert artifacts_layer > adapters_layer
    assert storage_layer > artifacts_layer


@pytest.mark.architecture
def test_storage_providers_sits_between_artifact_management_and_ml() -> None:
    artifacts_layer = PIPELINE_PACKAGES["artifact_management"]
    storage_layer = PIPELINE_PACKAGES["storage_providers"]
    ml_layer = PIPELINE_PACKAGES["ml"]
    assert storage_layer > artifacts_layer
    assert ml_layer > storage_layer


@pytest.mark.architecture
def test_framework_adapters_sits_between_ml_engine_plugins_and_artifact_management() -> None:
    plugins_layer = PIPELINE_PACKAGES["ml_engine_plugins"]
    adapters_layer = PIPELINE_PACKAGES["framework_adapters"]
    artifacts_layer = PIPELINE_PACKAGES["artifact_management"]
    assert adapters_layer > plugins_layer
    assert artifacts_layer > adapters_layer


@pytest.mark.architecture
def test_ml_engine_plugins_sits_between_ml_runtime_and_framework_adapters() -> None:
    runtime_layer = PIPELINE_PACKAGES["ml_runtime"]
    plugins_layer = PIPELINE_PACKAGES["ml_engine_plugins"]
    adapters_layer = PIPELINE_PACKAGES["framework_adapters"]
    assert plugins_layer > runtime_layer
    assert adapters_layer > plugins_layer


@pytest.mark.architecture
def test_ml_runtime_sits_between_inference_pipeline_and_ml() -> None:
    inference_layer = PIPELINE_PACKAGES["inference_pipeline"]
    runtime_layer = PIPELINE_PACKAGES["ml_runtime"]
    ml_layer = PIPELINE_PACKAGES["ml"]
    assert runtime_layer > inference_layer
    assert ml_layer > runtime_layer


@pytest.mark.architecture
def test_inference_pipeline_sits_between_model_registry_and_ml() -> None:
    registry_layer = PIPELINE_PACKAGES["model_registry"]
    inference_layer = PIPELINE_PACKAGES["inference_pipeline"]
    ml_layer = PIPELINE_PACKAGES["ml"]
    assert inference_layer > registry_layer
    assert ml_layer > inference_layer


@pytest.mark.architecture
def test_inference_pipeline_sits_between_model_registry_and_ml_runtime() -> None:
    registry_layer = PIPELINE_PACKAGES["model_registry"]
    inference_layer = PIPELINE_PACKAGES["inference_pipeline"]
    runtime_layer = PIPELINE_PACKAGES["ml_runtime"]
    assert inference_layer > registry_layer
    assert runtime_layer > inference_layer


@pytest.mark.architecture
def test_model_registry_sits_between_training_pipeline_and_ml() -> None:
    training_layer = PIPELINE_PACKAGES["training_pipeline"]
    registry_layer = PIPELINE_PACKAGES["model_registry"]
    ml_layer = PIPELINE_PACKAGES["ml"]
    assert registry_layer > training_layer
    assert ml_layer > registry_layer


@pytest.mark.architecture
def test_model_registry_sits_between_training_pipeline_and_inference_pipeline() -> None:
    training_layer = PIPELINE_PACKAGES["training_pipeline"]
    registry_layer = PIPELINE_PACKAGES["model_registry"]
    inference_layer = PIPELINE_PACKAGES["inference_pipeline"]
    assert registry_layer > training_layer
    assert inference_layer > registry_layer


@pytest.mark.architecture
def test_training_pipeline_sits_between_feature_store_and_model_registry() -> None:
    store_layer = PIPELINE_PACKAGES["feature_store"]
    training_layer = PIPELINE_PACKAGES["training_pipeline"]
    registry_layer = PIPELINE_PACKAGES["model_registry"]
    assert training_layer > store_layer
    assert registry_layer > training_layer


@pytest.mark.architecture
def test_feature_engineering_sits_between_market_data_and_connectors() -> None:
    market_data_layer = PIPELINE_PACKAGES["market_data"]
    feature_layer = PIPELINE_PACKAGES["feature_engineering"]
    connectors_layer = PIPELINE_PACKAGES["connectors"]
    assert feature_layer > market_data_layer
    assert connectors_layer > feature_layer


@pytest.mark.architecture
def test_connectors_import_historical_layer() -> None:
    connectors_layer = PIPELINE_PACKAGES["connectors"]
    historical_layer = PIPELINE_PACKAGES["historical"]
    assert connectors_layer > historical_layer


@pytest.mark.architecture
def test_project_root_exists() -> None:
    assert (PROJECT_ROOT / "architecture" / "dependency_rules.py").is_file()
