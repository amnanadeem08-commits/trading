"""Output normalization for framework-independent responses."""

from __future__ import annotations

import time

from inference_pipeline.runtime.input_schema import OutputType


class NormalizedOutput:
    """Framework-independent normalized inference output."""

    __slots__ = (
        "duration_ms",
        "label",
        "output_type",
        "probabilities",
        "raw_outputs",
        "values",
    )

    def __init__(
        self,
        *,
        output_type: OutputType,
        values: list[float],
        probabilities: list[float] | None = None,
        label: int | None = None,
        raw_outputs: list[object] | None = None,
        duration_ms: float = 0.0,
    ) -> None:
        self.output_type = output_type
        self.values = values
        self.probabilities = probabilities
        self.label = label
        self.raw_outputs = raw_outputs or []
        self.duration_ms = duration_ms

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "output_type": self.output_type.value,
            "values": self.values,
            "raw_outputs": self.raw_outputs,
        }
        if self.probabilities is not None:
            payload["probabilities"] = self.probabilities
        if self.label is not None:
            payload["label"] = self.label
        return payload


class OutputNormalizer:
    """Normalizes executor outputs into framework-independent structures."""

    def normalize(
        self,
        *,
        output_type: OutputType,
        raw_outputs: list[object],
    ) -> NormalizedOutput:
        started = time.monotonic() * 1000.0
        flat_values = self._flatten_values(raw_outputs)
        probabilities: list[float] | None = None
        label: int | None = None

        if output_type == OutputType.REGRESSION:
            values = flat_values[:1] if flat_values else [0.0]
        elif output_type == OutputType.BINARY_CLASSIFICATION:
            probabilities = self._to_probabilities(flat_values, expected=2)
            values = probabilities[:1]
            label = 1 if values and values[0] >= 0.5 else 0
        elif output_type in {OutputType.MULTICLASS, OutputType.PROBABILITY_VECTOR}:
            probabilities = self._to_probabilities(flat_values)
            label = self._argmax(probabilities) if probabilities else None
            values = [float(label if label is not None else 0)]
        else:
            values = flat_values

        duration_ms = max(0.0, time.monotonic() * 1000.0 - started)
        return NormalizedOutput(
            output_type=output_type,
            values=values,
            probabilities=probabilities,
            label=label,
            raw_outputs=raw_outputs,
            duration_ms=duration_ms,
        )

    @staticmethod
    def _flatten_values(raw_outputs: list[object]) -> list[float]:
        values: list[float] = []
        for item in raw_outputs:
            if isinstance(item, list):
                for nested in item:
                    if isinstance(nested, list):
                        values.extend(
                            float(value) for value in nested if isinstance(value, (int, float))
                        )
                    elif isinstance(nested, (int, float)):
                        values.append(float(nested))
            elif isinstance(item, (int, float)):
                values.append(float(item))
        return values

    @staticmethod
    def _to_probabilities(values: list[float], *, expected: int | None = None) -> list[float]:
        if not values:
            return []
        if expected is not None and len(values) < expected:
            padded = list(values) + [0.0] * (expected - len(values))
            values = padded
        total = sum(abs(value) for value in values)
        if total <= 0:
            return [1.0 / len(values)] * len(values)
        return [abs(value) / total for value in values]

    @staticmethod
    def _argmax(values: list[float]) -> int:
        return max(range(len(values)), key=lambda index: values[index])
