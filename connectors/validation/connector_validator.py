"""Connector validation framework."""

from __future__ import annotations

from connectors.adapters.adapter_metadata import AdapterMetadata
from connectors.validation.validation_result import ConnectorValidationResult
from connectors.versioning.connector_version import ConnectorVersion


class ConnectorValidator:
    """Validates adapter compatibility, version, and capabilities."""

    def __init__(self, version: ConnectorVersion | None = None) -> None:
        self._version = version

    def validate(
        self,
        *,
        adapter_id: str,
        metadata: AdapterMetadata | None,
        required_capabilities: tuple[str, ...] = (),
    ) -> ConnectorValidationResult:
        """Validate adapter metadata, capabilities, and version compatibility."""
        checks: dict[str, bool] = {}
        errors: list[str] = []
        warnings: list[str] = []

        checks["metadata_present"] = metadata is not None
        if metadata is None:
            errors.append("Adapter metadata is required")
        elif metadata.adapter_id != adapter_id:
            errors.append("Adapter id mismatch")
            checks["adapter_id_match"] = False
        else:
            checks["adapter_id_match"] = True

        capabilities_valid = True
        if metadata is not None and required_capabilities:
            available = set(metadata.capabilities)
            missing = [cap for cap in required_capabilities if cap not in available]
            capabilities_valid = not missing
            checks["capabilities_valid"] = capabilities_valid
            if missing:
                errors.append(f"Missing capabilities: {', '.join(missing)}")
        else:
            checks["capabilities_valid"] = True

        version_compatible = True
        if self._version is not None:
            version_compatible = self._version.is_compatible()
        checks["version_compatible"] = version_compatible
        if not version_compatible:
            errors.append("Connector version is not compatible with platform")

        valid = not errors
        return ConnectorValidationResult(
            valid=valid,
            adapter_id=adapter_id,
            checks=checks,
            errors=tuple(errors),
            warnings=tuple(warnings),
            version_compatible=version_compatible,
            capabilities_valid=capabilities_valid,
        )
