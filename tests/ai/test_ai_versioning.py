"""Unit tests for AI versioning."""

from __future__ import annotations

import pytest

from ai import AIVersion
from versioning.prompt_registry import reset_prompt_registry


@pytest.fixture(autouse=True)
def _reset_version_registry() -> None:
    reset_prompt_registry()
    yield
    reset_prompt_registry()


@pytest.mark.unit
def test_ai_version_register_and_list() -> None:
    version = AIVersion(
        artifact_id="sample-agent",
        version_id="1.0.0",
        artifact_type="agent",
        description="initial",
    )
    version.register()
    versions = AIVersion.list_versions()
    assert len(versions) == 1
    assert versions[0].version_id == "1.0.0"
