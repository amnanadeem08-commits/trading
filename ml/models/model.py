"""ML model domain contracts."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from ml.evaluation.evaluation_result import EvaluationResult
from ml.inference.prediction_result import PredictionResult
from ml.models.model_metadata import ModelMetadata
from ml.training.training_result import TrainingResult
from models.common import PlatformModel


class ModelArtifact(PlatformModel):
    """Serialized model artifact reference."""

    artifact_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    uri: str = Field(min_length=1, default="memory://artifact")
    checksum: str = Field(min_length=1, default="")
    attributes: dict[str, str] = Field(default_factory=dict)


class MLModel(ABC):
    """Executable ML model implementation contract."""

    @abstractmethod
    def model_id(self) -> str:
        """Return the model identifier."""

    @abstractmethod
    def name(self) -> str:
        """Return the model display name."""

    @abstractmethod
    def version(self) -> str:
        """Return the model version."""

    def metadata(self) -> ModelMetadata:
        """Return model metadata."""
        return ModelMetadata(
            model_id=self.model_id(),
            name=self.name(),
            version=self.version(),
        )

    def artifact(self) -> ModelArtifact:
        """Return the model artifact reference."""
        return ModelArtifact(
            artifact_id=f"{self.model_id()}-{self.version()}",
            model_id=self.model_id(),
            version=self.version(),
        )

    @abstractmethod
    def train(self, *, dataset_id: str, parameters: dict[str, Any]) -> TrainingResult:
        """Train the model using a dataset reference."""

    @abstractmethod
    def predict(self, *, inputs: tuple[dict[str, Any], ...]) -> PredictionResult:
        """Run inference on input records."""

    def evaluate(
        self,
        *,
        dataset_id: str,
        predictions: tuple[dict[str, Any], ...],
    ) -> EvaluationResult:
        """Evaluate model outputs against a dataset reference."""
        raise NotImplementedError
