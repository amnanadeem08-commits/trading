"""Feature extraction pipeline."""

from __future__ import annotations

from threading import RLock
from uuid import uuid4

from feature_engineering.extraction.extraction_context import FeatureExtractionContext
from feature_engineering.extraction.extraction_result import FeatureExtractionResult
from feature_engineering.extraction.extractor import AttributeFeatureExtractor, FeatureExtractor
from feature_engineering.models.feature_batch import FeatureBatch
from feature_engineering.models.feature_metadata import FeatureMetadata
from feature_engineering.models.feature_set import FeatureSet
from feature_engineering.models.feature_vector import FeatureVector
from feature_engineering.models.feature_window import FeatureWindow
from market_data.models.market_record import MarketRecord
from market_data.stream.stream_buffer import StreamBuffer


class FeatureExtractionPipeline:
    """Transforms market records into ML-ready feature structures."""

    def __init__(
        self,
        context: FeatureExtractionContext,
        *,
        extractor: FeatureExtractor | None = None,
        stream_buffer: StreamBuffer | None = None,
        records: tuple[MarketRecord, ...] = (),
    ) -> None:
        self._context = context
        self._extractor = extractor or AttributeFeatureExtractor()
        self._stream_buffer = stream_buffer
        self._records = records
        self._lock = RLock()
        self._position = 0

    @property
    def context(self) -> FeatureExtractionContext:
        return self._context

    @property
    def extractor(self) -> FeatureExtractor:
        return self._extractor

    def extract_vector(self, record: MarketRecord) -> FeatureVector:
        """Extract a single feature vector from a market record."""
        return self._extractor.extract(record, context=self._context)

    def extract_batch(self, *, page: int = 0) -> FeatureBatch:
        """Extract a batch of feature vectors."""
        vectors: list[FeatureVector] = []
        if self._stream_buffer is not None:
            batch = self._stream_buffer.page(page=page, page_size=self._context.batch_size)
            for record in batch.records:
                vectors.append(self.extract_vector(record))
            return FeatureBatch(
                batch_id=str(uuid4()),
                pipeline_id=self._context.pipeline_id,
                dataset_id=self._context.dataset_id,
                symbol_id=self._context.symbol_id,
                vectors=tuple(vectors),
                offset=batch.offset,
                total=batch.total,
                completed=batch.completed,
            )

        start = page * self._context.batch_size
        end = min(start + self._context.batch_size, len(self._records))
        if start >= len(self._records):
            return FeatureBatch(
                batch_id=str(uuid4()),
                pipeline_id=self._context.pipeline_id,
                dataset_id=self._context.dataset_id,
                symbol_id=self._context.symbol_id,
                vectors=(),
                offset=start,
                total=len(self._records),
                completed=True,
            )
        for record in self._records[start:end]:
            vectors.append(self.extract_vector(record))
        return FeatureBatch(
            batch_id=str(uuid4()),
            pipeline_id=self._context.pipeline_id,
            dataset_id=self._context.dataset_id,
            symbol_id=self._context.symbol_id,
            vectors=tuple(vectors),
            offset=start,
            total=len(self._records),
            completed=end >= len(self._records),
        )

    def extract_set(self, *, page: int = 0) -> FeatureSet:
        """Extract a feature set from the current batch."""
        batch = self.extract_batch(page=page)
        metadata = FeatureMetadata(
            feature_set_id=f"set-{self._context.pipeline_id}",
            dataset_id=self._context.dataset_id,
            symbol_id=self._context.symbol_id,
            schema_id=self._context.schema_id,
            version=self._context.version,
            extractor_id=self._extractor.extractor_id(),
            feature_count=len(batch.vectors[0].features) if batch.vectors else 0,
            record_count=len(batch.vectors),
        )
        return FeatureSet(
            feature_set_id=metadata.feature_set_id,
            vectors=batch.vectors,
            metadata=metadata,
        )

    def extract_window(self, *, size: int | None = None) -> FeatureWindow:
        """Extract a sliding window of feature vectors."""
        window_size = size or self._context.window_size
        vectors: list[FeatureVector] = []
        if self._stream_buffer is not None:
            records = self._stream_buffer.window(size=window_size)
            for record in records:
                vectors.append(self.extract_vector(record))
        else:
            with self._lock:
                end = min(self._position + window_size, len(self._records))
                slice_records = self._records[self._position : end]
            for record in slice_records:
                vectors.append(self.extract_vector(record))
        return FeatureWindow(
            window_id=str(uuid4()),
            dataset_id=self._context.dataset_id,
            symbol_id=self._context.symbol_id,
            vectors=tuple(vectors),
            window_size=window_size,
            offset=self._position,
        )

    def run(self, *, max_batches: int = 1) -> FeatureExtractionResult:
        """Run extraction for one or more batches."""
        all_vectors: list[FeatureVector] = []
        completed = False
        for page in range(max_batches):
            batch = self.extract_batch(page=page)
            all_vectors.extend(batch.vectors)
            completed = batch.completed
            if batch.completed:
                break
        feature_set = None
        if all_vectors:
            metadata = FeatureMetadata(
                feature_set_id=f"set-{self._context.pipeline_id}",
                dataset_id=self._context.dataset_id,
                symbol_id=self._context.symbol_id,
                schema_id=self._context.schema_id,
                version=self._context.version,
                extractor_id=self._extractor.extractor_id(),
                feature_count=len(all_vectors[0].features),
                record_count=len(all_vectors),
            )
            feature_set = FeatureSet(
                feature_set_id=metadata.feature_set_id,
                vectors=tuple(all_vectors),
                metadata=metadata,
            )
        last_batch = self.extract_batch(page=max(0, max_batches - 1)) if max_batches > 0 else None
        return FeatureExtractionResult(
            pipeline_id=self._context.pipeline_id,
            dataset_id=self._context.dataset_id,
            symbol_id=self._context.symbol_id,
            batch=last_batch,
            feature_set=feature_set,
            vectors_extracted=len(all_vectors),
            completed=completed,
        )

    def next_from_stream(self) -> FeatureVector | None:
        """Extract the next vector from an attached stream buffer."""
        if self._stream_buffer is None:
            return None
        step = self._stream_buffer.next()
        if step is None or step.record is None:
            return None
        return self.extract_vector(step.record)
