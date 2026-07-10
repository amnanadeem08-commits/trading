"""Historical query engine."""

from __future__ import annotations

from historical.datasets.historical_dataset import HistoricalDataset
from historical.exceptions import QueryError
from historical.query.filters import QueryFilters
from historical.query.query_request import QueryRequest, QueryType
from historical.query.query_result import QueryResult
from historical.storage.repository import Repository
from historical.storage.repository_record import RepositoryRecord
from models.common import UTCDateTime


class QueryEngine:
    """In-memory query engine for historical datasets."""

    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    def execute(self, request: QueryRequest) -> QueryResult:
        """Execute a historical query request."""
        filters = request.filters
        if request.query_type == QueryType.BY_ID:
            return self._query_by_id(filters)
        if request.query_type == QueryType.BY_VERSION:
            return self._query_by_version(filters)
        if request.query_type == QueryType.TIME_RANGE:
            return self._query_time_range(filters)
        if request.query_type == QueryType.METADATA:
            return self._query_metadata(filters)
        if request.query_type == QueryType.TAG:
            return self._query_tags(filters)
        if request.query_type == QueryType.CURSOR:
            return self._query_cursor(filters)
        msg = f"Unsupported query type: {request.query_type}"
        raise QueryError(msg)

    def lookup_by_id(self, dataset_id: str) -> QueryResult:
        return self.execute(
            QueryRequest(
                query_type=QueryType.BY_ID,
                filters=QueryFilters(dataset_id=dataset_id),
            )
        )

    def lookup_by_version(self, dataset_id: str, *, version: str) -> QueryResult:
        return self.execute(
            QueryRequest(
                query_type=QueryType.BY_VERSION,
                filters=QueryFilters(dataset_id=dataset_id, version=version),
            )
        )

    def query_time_range(
        self,
        dataset_id: str,
        *,
        start_timestamp: UTCDateTime | None,
        end_timestamp: UTCDateTime | None,
        version: str | None = None,
    ) -> QueryResult:
        return self.execute(
            QueryRequest(
                query_type=QueryType.TIME_RANGE,
                filters=QueryFilters(
                    dataset_id=dataset_id,
                    version=version,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                ),
            )
        )

    def _query_by_id(self, filters: QueryFilters) -> QueryResult:
        if filters.dataset_id is None:
            msg = "dataset_id is required"
            raise QueryError(msg)
        dataset = self._repository.get_dataset(filters.dataset_id)
        records = self._repository.load(filters.dataset_id)
        return QueryResult(
            matched=True,
            datasets=(dataset,),
            records=records,
            metadata=(dataset.metadata,),
            total=len(records),
        )

    def _query_by_version(self, filters: QueryFilters) -> QueryResult:
        if filters.dataset_id is None or filters.version is None:
            msg = "dataset_id and version are required"
            raise QueryError(msg)
        dataset = self._repository.get_dataset(filters.dataset_id)
        records = self._repository.load(filters.dataset_id, version=filters.version)
        return QueryResult(
            matched=True,
            datasets=(dataset,),
            records=records,
            metadata=(dataset.metadata,),
            total=len(records),
        )

    def _query_time_range(self, filters: QueryFilters) -> QueryResult:
        if filters.dataset_id is None:
            msg = "dataset_id is required"
            raise QueryError(msg)
        records = self._repository.load(filters.dataset_id, version=filters.version)
        filtered = self._filter_records_by_time(records, filters)
        dataset = self._repository.get_dataset(filters.dataset_id)
        return QueryResult(
            matched=len(filtered) > 0,
            datasets=(dataset,),
            records=filtered,
            metadata=(dataset.metadata,),
            total=len(filtered),
        )

    def _query_metadata(self, filters: QueryFilters) -> QueryResult:
        datasets: list[HistoricalDataset] = []
        metadata = []
        for dataset_id in self._repository.list():
            dataset = self._repository.get_dataset(dataset_id)
            if filters.metadata_key is not None:
                value = dataset.metadata.attributes.get(filters.metadata_key)
                if filters.metadata_value is not None and value != filters.metadata_value:
                    continue
            datasets.append(dataset)
            metadata.append(dataset.metadata)
        return QueryResult(
            matched=bool(datasets),
            datasets=tuple(datasets),
            metadata=tuple(metadata),
            total=len(datasets),
        )

    def _query_tags(self, filters: QueryFilters) -> QueryResult:
        datasets: list[HistoricalDataset] = []
        metadata = []
        required_tags = set(filters.tags)
        for dataset_id in self._repository.list():
            dataset = self._repository.get_dataset(dataset_id)
            if required_tags and not required_tags.issubset(set(dataset.tags)):
                continue
            datasets.append(dataset)
            metadata.append(dataset.metadata)
        return QueryResult(
            matched=bool(datasets),
            datasets=tuple(datasets),
            metadata=tuple(metadata),
            total=len(datasets),
        )

    def _query_cursor(self, filters: QueryFilters) -> QueryResult:
        if filters.dataset_id is None or filters.cursor_position is None:
            msg = "dataset_id and cursor_position are required"
            raise QueryError(msg)
        records = self._repository.load(filters.dataset_id, version=filters.version)
        position = filters.cursor_position
        if position >= len(records):
            return QueryResult(matched=False, total=len(records), cursor_position=position)
        selected = (records[position],)
        dataset = self._repository.get_dataset(filters.dataset_id)
        return QueryResult(
            matched=True,
            datasets=(dataset,),
            records=selected,
            metadata=(dataset.metadata,),
            cursor_position=position,
            total=len(records),
        )

    @staticmethod
    def _filter_records_by_time(
        records: tuple[RepositoryRecord, ...],
        filters: QueryFilters,
    ) -> tuple[RepositoryRecord, ...]:
        filtered: list[RepositoryRecord] = []
        for record in records:
            if filters.start_timestamp is not None and record.timestamp < filters.start_timestamp:
                continue
            if filters.end_timestamp is not None and record.timestamp > filters.end_timestamp:
                continue
            filtered.append(record)
        return tuple(filtered)
