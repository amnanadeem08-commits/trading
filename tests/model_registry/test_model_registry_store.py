"""Unit tests for model registry."""

from __future__ import annotations

import pytest

from model_registry import ModelNotFoundError, ModelRegistrationError, ModelRegistry
from tests.model_registry_helpers import make_registered_model


@pytest.mark.unit
def test_register_model() -> None:
    registry = ModelRegistry()
    model = make_registered_model()
    registered = registry.register_model(model)
    assert registry.lookup("model-1").model_id == registered.model_id


@pytest.mark.unit
def test_register_model_max_limit() -> None:
    registry = ModelRegistry(max_registered_models=1)
    registry.register_model(make_registered_model(model_id="model-1"))
    with pytest.raises(ModelRegistrationError):
        registry.register_model(make_registered_model(model_id="model-2", name="Other"))


@pytest.mark.unit
def test_lookup_missing_raises() -> None:
    registry = ModelRegistry()
    with pytest.raises(ModelNotFoundError):
        registry.lookup("missing")
