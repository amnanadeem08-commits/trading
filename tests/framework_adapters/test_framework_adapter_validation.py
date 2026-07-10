"""Unit tests for framework adapter validator."""

from __future__ import annotations

import pytest

from framework_adapters import (
    AdapterRegistry,
    AdapterValidationError,
    FrameworkAdapterValidator,
)
from tests.framework_adapters_helpers import make_stub_framework_adapter


@pytest.mark.unit
def test_validator_accepts_stub_adapter() -> None:
    validator = FrameworkAdapterValidator()
    result = validator.validate_adapter(make_stub_framework_adapter())
    assert result.valid is True


@pytest.mark.unit
def test_validator_rejects_duplicate_registration() -> None:
    registry = AdapterRegistry()
    validator = FrameworkAdapterValidator(registry=registry)
    adapter = make_stub_framework_adapter()
    registry.register(adapter)
    result = validator.validate_adapter(adapter)
    assert result.valid is False


@pytest.mark.unit
def test_validator_ensure_valid_raises() -> None:
    validator = FrameworkAdapterValidator()
    adapter = make_stub_framework_adapter(adapter_id="")
    result = validator.validate_adapter(adapter)
    with pytest.raises(AdapterValidationError):
        validator.ensure_valid(result)
