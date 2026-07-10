"""Registered model contract."""

from __future__ import annotations

from model_registry.models.model_metadata import ModelMetadata
from model_registry.models.model_status import ModelStatus
from models.common import PlatformModel, utc_now


class RegisteredModel(PlatformModel):
    """Logical model registered in the model registry."""

    metadata: ModelMetadata
    status: ModelStatus = ModelStatus.ACTIVE
    latest_version_id: str | None = None

    @classmethod
    def create(
        cls,
        *,
        model_id: str,
        name: str,
        description: str = "",
        owner: str = "platform",
        tags: tuple[str, ...] = (),
    ) -> RegisteredModel:
        now = utc_now()
        metadata = ModelMetadata(
            model_id=model_id,
            name=name,
            description=description,
            owner=owner,
            tags=tags,
            created_at=now,
            updated_at=now,
        )
        return cls(metadata=metadata)

    @property
    def model_id(self) -> str:
        return self.metadata.model_id
