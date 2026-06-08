"""Taxi 합성 결함 케이스."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb

from project_pivot.taxi_data.errors import SyntheticCaseError
from project_pivot.taxi_data.sql import quote_identifier
from project_pivot.taxi_data.synthetic.source import (
    parquet_columns,
    require_columns,
    source_parameter,
)
from project_pivot.taxi_data.synthetic.sql import (
    rename_clause,
    replace_text_clause,
    sampled_source_query,
)
from project_pivot.taxi_data.synthetic.writer import write_partitioned_case


def write_normal_case(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    sample_fraction: float = 0.2,
    timestamp_column: str = "tpep_pickup_datetime",
    partition_column: str = "pickup_date",
    observed_at: datetime | None = None,
) -> Path:
    """정상 기준 파티션 파일을 생성한다."""

    validate_fraction(sample_fraction, "sample_fraction")
    observed_at_value = observed_at or datetime.now(UTC)
    query = sampled_source_query(
        timestamp_column=timestamp_column,
        partition_column=partition_column,
    )
    query = f"""
        WITH sampled AS ({query})
        SELECT *, ? AS "observed_at"
        FROM sampled
    """
    return write_partitioned_case(
        connection=connection,
        case_name="normal",
        output_root=output_root,
        query=query,
        params=[
            source_parameter(source_paths),
            sample_fraction,
            observed_at_value,
        ],
        partition_column=partition_column,
    )


def row_count_drop(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    sample_fraction: float = 0.1,
    timestamp_column: str = "tpep_pickup_datetime",
    partition_column: str = "pickup_date",
) -> Path:
    """일자 분포를 보존하며 행 수를 대폭 줄인 파티션 파일을 생성한다."""

    validate_fraction(sample_fraction, "sample_fraction")
    query = sampled_source_query(
        timestamp_column=timestamp_column,
        partition_column=partition_column,
    )
    return write_partitioned_case(
        connection=connection,
        case_name="row_count_drop",
        output_root=output_root,
        query=query,
        params=[source_parameter(source_paths), sample_fraction],
        partition_column=partition_column,
    )


def null_spike(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    target_column: str = "total_amount",
    null_fraction: float = 0.2,
    sample_fraction: float = 0.2,
    timestamp_column: str = "tpep_pickup_datetime",
    partition_column: str = "pickup_date",
) -> Path:
    """특정 컬럼의 Null 비율이 급증한 파티션 파일을 생성한다."""

    validate_fraction(null_fraction, "null_fraction")
    validate_fraction(sample_fraction, "sample_fraction")
    require_columns(connection, source_paths, {target_column})
    target = quote_identifier(target_column)
    sampled_query = sampled_source_query(
        timestamp_column=timestamp_column,
        partition_column=partition_column,
    )
    query = f"""
        WITH sampled AS ({sampled_query}),
        ranked AS (
            SELECT
                *,
                row_number() OVER (
                    PARTITION BY {quote_identifier(partition_column)}
                    ORDER BY {quote_identifier(timestamp_column)}
                ) AS __null_rank,
                count(*) OVER (
                    PARTITION BY {quote_identifier(partition_column)}
                ) AS __partition_count
            FROM sampled
        )
        SELECT
            * EXCLUDE (__null_rank, __partition_count)
              REPLACE (
                CASE
                    WHEN __null_rank <= greatest(
                        1,
                        CAST(ceil(__partition_count * ?) AS BIGINT)
                    )
                    THEN NULL
                    ELSE {target}
                END AS {target}
              )
        FROM ranked
    """
    return write_partitioned_case(
        connection=connection,
        case_name="null_spike",
        output_root=output_root,
        query=query,
        params=[source_parameter(source_paths), sample_fraction, null_fraction],
        partition_column=partition_column,
    )


def schema_drift(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    text_columns: Sequence[str] = ("total_amount",),
    renamed_columns: Mapping[str, str] | None = None,
    sample_fraction: float = 0.2,
    timestamp_column: str = "tpep_pickup_datetime",
    partition_column: str = "pickup_date",
) -> Path:
    """컬럼 타입 또는 이름이 달라진 스키마 드리프트 파티션 파일을 생성한다."""

    validate_fraction(sample_fraction, "sample_fraction")
    renamed_columns = renamed_columns or {}
    overlap = set(text_columns).intersection(renamed_columns)
    if overlap:
        msg = (
            "같은 컬럼을 동시에 타입 변경 및 이름 변경할 수 없습니다: "
            f"{sorted(overlap)}"
        )
        raise SyntheticCaseError(msg)
    require_columns(connection, source_paths, {*text_columns, *renamed_columns})
    sampled_query = sampled_source_query(
        timestamp_column=timestamp_column,
        partition_column=partition_column,
    )
    query = f"""
        WITH sampled AS ({sampled_query})
        SELECT *{replace_text_clause(text_columns)}{rename_clause(renamed_columns)}
        FROM sampled
    """
    return write_partitioned_case(
        connection=connection,
        case_name="schema_drift",
        output_root=output_root,
        query=query,
        params=[source_parameter(source_paths), sample_fraction],
        partition_column=partition_column,
    )


def freshness_delay(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    observed_at: datetime | None = None,
    delay_days: int = 30,
    sample_fraction: float = 0.2,
    timestamp_column: str = "tpep_pickup_datetime",
    partition_column: str = "pickup_date",
) -> Path:
    """observed_at을 오래된 시각으로 밀어 지연 파티션 파일을 생성한다."""

    validate_fraction(sample_fraction, "sample_fraction")
    observed_at_value = observed_at or datetime.now(UTC) - timedelta(days=delay_days)
    sampled_query = sampled_source_query(
        timestamp_column=timestamp_column,
        partition_column=partition_column,
    )
    has_observed_at = "observed_at" in parquet_columns(connection, source_paths)
    if has_observed_at:
        observed_at_projection = """
            * REPLACE (? AS "observed_at")
        """
    else:
        observed_at_projection = """
            *,
            ? AS "observed_at"
        """
    query = f"""
        WITH sampled AS ({sampled_query})
        SELECT {observed_at_projection}
        FROM sampled
    """
    return write_partitioned_case(
        connection=connection,
        case_name="freshness_delay",
        output_root=output_root,
        query=query,
        params=[source_parameter(source_paths), sample_fraction, observed_at_value],
        partition_column=partition_column,
    )


def validate_fraction(value: float, name: str) -> None:
    if not 0 < value <= 1:
        msg = f"{name}은 0보다 크고 1 이하이어야 합니다: {value}"
        raise SyntheticCaseError(msg)
