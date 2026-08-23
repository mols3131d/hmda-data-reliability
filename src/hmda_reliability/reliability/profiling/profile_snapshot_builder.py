"""Build read-only partition metrics with table-wide schema identity from DuckDB."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, date, datetime, time
from typing import Any

import duckdb

from hmda_reliability.data_platform.sql import qualify_table_name, quote_identifier
from hmda_reliability.reliability.contracts import (
    FreshnessMeasurementStatus,
    ProfileSnapshot,
)
from hmda_reliability.reliability.errors import ProfileSnapshotError
from hmda_reliability.reliability.profiling.profile_snapshot_request import (
    ProfileSnapshotRequest,
)


class DuckDBProfileSnapshotBuilder:
    """Build partition metrics plus the table-wide schema hash."""

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    def build(self, request: ProfileSnapshotRequest) -> ProfileSnapshot:
        """Return measured partition metrics without inventing freshness."""

        try:
            schema_hash = calculate_schema_hash(self._connection, request.table_name)
            profile_columns = _resolve_profile_columns(
                self._connection,
                request.table_name,
                request.profile_columns,
            )
            metrics = _calculate_partition_metrics(
                self._connection,
                request=request,
                profile_columns=profile_columns,
            )
        except duckdb.Error as exc:
            msg = (
                "profile snapshot 계산에 실패했습니다: "
                f"table={request.table_name}, "
                f"partition={_partition_label(request.partition)}"
            )
            raise ProfileSnapshotError(msg) from exc

        return ProfileSnapshot(
            snapshot_id=_snapshot_id(request.asset_name, request.partition),
            asset_name=request.asset_name,
            partition=_partition_label(request.partition),
            observed_at=request.observed_at,
            row_count=metrics.row_count,
            null_rates=metrics.null_rates,
            schema_hash=schema_hash,
            freshness_at=metrics.freshness_at,
            freshness_status=metrics.freshness_status,
            metric_values=metrics.metric_values,
        )


def create_profile_snapshot(
    connection: duckdb.DuckDBPyConnection,
    request: ProfileSnapshotRequest,
) -> ProfileSnapshot:
    """Build a snapshot, wrapping DuckDB failures as ProfileSnapshotError."""

    return DuckDBProfileSnapshotBuilder(connection).build(request)


def calculate_schema_hash(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> str:
    """Hash name-sorted column names and types; row data is not included."""

    rows = connection.execute(f"DESCRIBE {qualify_table_name(table_name)}").fetchall()
    schema = sorted(
        (
            {
                "name": str(row[0]),
                "type": str(row[1]),
            }
            for row in rows
        ),
        key=lambda item: item["name"],
    )
    payload = json.dumps(
        schema,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


class _PartitionMetrics:
    def __init__(
        self,
        *,
        row_count: int,
        null_rates: dict[str, float],
        freshness_at: datetime | None,
        freshness_status: FreshnessMeasurementStatus,
        metric_values: dict[str, float],
    ) -> None:
        self.row_count = row_count
        self.null_rates = null_rates
        self.freshness_at = freshness_at
        self.freshness_status = freshness_status
        self.metric_values = metric_values


def _resolve_profile_columns(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    profile_columns: tuple[str, ...],
) -> tuple[str, ...]:
    if profile_columns:
        return profile_columns
    rows = connection.execute(f"DESCRIBE {qualify_table_name(table_name)}").fetchall()
    return tuple(str(row[0]) for row in rows)


def _calculate_partition_metrics(
    connection: duckdb.DuckDBPyConnection,
    *,
    request: ProfileSnapshotRequest,
    profile_columns: tuple[str, ...],
) -> _PartitionMetrics:
    select_parts = ["count(*) AS row_count"]
    select_parts.extend(_null_count_expression(column) for column in profile_columns)
    if request.freshness_column is not None:
        select_parts.append(
            f"max({quote_identifier(request.freshness_column)}) AS freshness_value"
        )
    partition_filter, partition_params = _partition_filter(request)

    result = connection.execute(
        f"""
        SELECT {", ".join(select_parts)}
        FROM {qualify_table_name(request.table_name)}
        WHERE {partition_filter}
        """,
        partition_params,
    ).fetchone()
    if result is None:
        msg = (
            "profile metric 조회 결과가 없습니다: "
            f"table={request.table_name}, "
            f"partition={_partition_label(request.partition)}"
        )
        raise ProfileSnapshotError(msg)

    row_count = int(result[0])
    null_counts = _extract_null_counts(result, profile_columns)
    null_rates = {
        column: _null_rate(null_count, row_count)
        for column, null_count in null_counts.items()
    }
    freshness_value = (
        result[1 + len(profile_columns)] if request.freshness_column else None
    )
    freshness_at = _normalize_freshness(freshness_value)
    if freshness_at is not None and freshness_at > request.observed_at:
        msg = (
            "freshness 값이 observed_at보다 미래입니다: "
            f"freshness_at={freshness_at.isoformat()}, "
            f"observed_at={request.observed_at.isoformat()}"
        )
        raise ProfileSnapshotError(msg)
    freshness_status = (
        FreshnessMeasurementStatus.MEASURED
        if freshness_at is not None
        else FreshnessMeasurementStatus.UNAVAILABLE
    )
    metric_values = _metric_values(
        row_count=row_count,
        null_counts=null_counts,
    )
    return _PartitionMetrics(
        row_count=row_count,
        null_rates=null_rates,
        freshness_at=freshness_at,
        freshness_status=freshness_status,
        metric_values=metric_values,
    )


def _null_count_expression(column: str) -> str:
    quoted_column = quote_identifier(column)
    alias = quote_identifier(f"{column}__null_count")
    return f"sum(CASE WHEN {quoted_column} IS NULL THEN 1 ELSE 0 END) AS {alias}"


def _extract_null_counts(
    row: tuple[Any, ...],
    profile_columns: tuple[str, ...],
) -> dict[str, int]:
    return {
        column: int(row[index + 1] or 0) for index, column in enumerate(profile_columns)
    }


def _null_rate(null_count: int, row_count: int) -> float:
    if row_count == 0:
        return 0.0
    return null_count / row_count


def _metric_values(
    *,
    row_count: int,
    null_counts: dict[str, int],
) -> dict[str, float]:
    values = {"row_count": float(row_count)}
    values.update(
        {
            f"{column}.null_count": float(null_count)
            for column, null_count in null_counts.items()
        }
    )
    return values


def _normalize_freshness(value: object) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=UTC)
    msg = f"freshness 값은 datetime/date여야 합니다: {type(value).__name__}"
    raise ProfileSnapshotError(msg)


def _partition_label(partition: date | int | str) -> str:
    if isinstance(partition, date):
        return partition.isoformat()
    return str(partition)


def _partition_filter(request: ProfileSnapshotRequest) -> tuple[str, list[object]]:
    quoted_column = quote_identifier(request.partition_column)
    if isinstance(request.partition, date):
        return f"CAST({quoted_column} AS DATE) = ?", [request.partition]
    return (
        f"CAST({quoted_column} AS VARCHAR) = ?",
        [_partition_label(request.partition)],
    )


def _snapshot_id(asset_name: str, partition: date | int | str) -> str:
    normalized_asset = "".join(
        character if character.isalnum() else "_" for character in asset_name.lower()
    ).strip("_")
    normalized_partition = _partition_label(partition).replace("-", "_")
    return f"profile_{normalized_asset}_{normalized_partition}"
