"""Unit tests for versioning registries."""

from __future__ import annotations

import pytest

from models.common import ContractViolationError, VersionInfo
from versioning import (
    VersionRegistry,
    get_connector_version_registry,
    get_model_registry,
    get_prompt_registry,
    get_schema_registry,
    get_strategy_registry,
    reset_connector_version_registry,
    reset_model_registry,
    reset_prompt_registry,
    reset_schema_registry,
    reset_strategy_registry,
)


@pytest.fixture(autouse=True)
def _reset_registries() -> None:
    reset_model_registry()
    reset_prompt_registry()
    reset_strategy_registry()
    reset_connector_version_registry()
    reset_schema_registry()
    yield
    reset_model_registry()
    reset_prompt_registry()
    reset_strategy_registry()
    reset_connector_version_registry()
    reset_schema_registry()


def _version(version_id: str) -> VersionInfo:
    return VersionInfo(version_id=version_id)


@pytest.mark.unit
def test_version_registry_register_and_get() -> None:
    registry = VersionRegistry("test")
    version = _version("1.0.0")
    registry.register(version)
    assert registry.get("1.0.0").version_id == "1.0.0"
    assert registry.current() is not None
    assert registry.current() == version


@pytest.mark.unit
def test_version_registry_missing_raises() -> None:
    registry = VersionRegistry("test")
    with pytest.raises(ContractViolationError):
        registry.get("9.9.9")


@pytest.mark.unit
def test_model_registry_singleton() -> None:
    registry = get_model_registry()
    registry.register(_version("model-1"))
    assert get_model_registry().exists("model-1") is True


@pytest.mark.unit
def test_all_named_registries_exist() -> None:
    get_model_registry().register(_version("m-1"))
    get_prompt_registry().register(_version("p-1"))
    get_strategy_registry().register(_version("s-1"))
    get_connector_version_registry().register(_version("c-1"))
    get_schema_registry().register(_version("sch-1"))

    assert get_model_registry().list_versions()[0].version_id == "m-1"
    assert get_prompt_registry().list_versions()[0].version_id == "p-1"
    assert get_strategy_registry().list_versions()[0].version_id == "s-1"
    assert get_connector_version_registry().list_versions()[0].version_id == "c-1"
    assert get_schema_registry().list_versions()[0].version_id == "sch-1"
