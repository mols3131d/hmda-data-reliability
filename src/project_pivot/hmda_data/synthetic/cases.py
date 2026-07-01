"""HMDA 합성 결함 케이스."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb

from project_pivot.data_platform.sql import quote_identifier
from project_pivot.hmda_data.errors import SyntheticCaseError
from project_pivot.hmda_data.synthetic.source import (
    require_columns,
    source_paths_parameter,
    source_union_sql,
)
from project_pivot.hmda_data.synthetic.writer import write_case_file


def row_count_drop(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    sample_fraction: float = 0.1,
) -> Path:
    """연도 분포를 보존하며 행 수를 대폭 줄인 파일을 생성한다."""

    validate_fraction(sample_fraction, "sample_fraction")
    query = _ranked_sample_query(source_paths)
    query = f"""
        WITH ranked AS ({query})
        SELECT * EXCLUDE (__sample_rank, __partition_count)
        FROM ranked
        WHERE __sample_rank <= greatest(
            1,
            CAST(ceil(__partition_count * ?) AS BIGINT)
        )
    """
    return write_case_file(
        connection=connection,
        case_name="row_count_drop",
        output_root=output_root,
        query=query,
        params=[*source_paths_parameter(source_paths), sample_fraction],
    )


def null_spike(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    target_column: str = "income",
    null_fraction: float = 0.2,
    sample_fraction: float = 1.0,
) -> Path:
    """핵심 분석 컬럼의 Null 비율이 급증한 파일을 생성한다."""

    validate_fraction(null_fraction, "null_fraction")
    validate_fraction(sample_fraction, "sample_fraction")
    require_columns(connection, source_paths, {target_column})
    target = quote_identifier(target_column)
    query = _ranked_sample_query(source_paths)
    query = f"""
        WITH ranked AS ({query}),
        sampled AS (
            SELECT *
            FROM ranked
            WHERE __sample_rank <= greatest(
                1,
                CAST(ceil(__partition_count * ?) AS BIGINT)
            )
        ),
        null_ranked AS (
            SELECT
                *,
                row_number() OVER (
                    PARTITION BY activity_year
                    ORDER BY __sample_rank
                ) AS __null_rank,
                count(*) OVER (
                    PARTITION BY activity_year
                ) AS __sample_count
            FROM sampled
        )
        SELECT
            * EXCLUDE (
                __sample_rank,
                __partition_count,
                __null_rank,
                __sample_count
            )
            REPLACE (
                CASE
                    WHEN __null_rank <= greatest(
                        1,
                        CAST(ceil(__sample_count * ?) AS BIGINT)
                    )
                    THEN NULL
                    ELSE {target}
                END AS {target}
            )
        FROM null_ranked
    """
    return write_case_file(
        connection=connection,
        case_name="null_spike",
        output_root=output_root,
        query=query,
        params=[*source_paths_parameter(source_paths), sample_fraction, null_fraction],
    )


def schema_drift(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    target_column: str = "loan_amount",
    sample_fraction: float = 1.0,
) -> Path:
    """핵심 컬럼 타입이 달라진 스키마 드리프트 파일을 생성한다."""

    validate_fraction(sample_fraction, "sample_fraction")
    require_columns(connection, source_paths, {target_column})
    target = quote_identifier(target_column)
    query = _ranked_sample_query(source_paths)
    query = f"""
        WITH ranked AS ({query})
        SELECT
            * EXCLUDE (__sample_rank, __partition_count)
            REPLACE (CAST({target} AS VARCHAR) AS {target})
        FROM ranked
        WHERE __sample_rank <= greatest(
            1,
            CAST(ceil(__partition_count * ?) AS BIGINT)
        )
    """
    return write_case_file(
        connection=connection,
        case_name="schema_drift",
        output_root=output_root,
        query=query,
        params=[*source_paths_parameter(source_paths), sample_fraction],
    )


def freshness_delay(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    observed_at: datetime | None = None,
    delay_days: int = 30,
    sample_fraction: float = 1.0,
) -> Path:
    """observed_at을 오래된 시각으로 밀어 지연 파일을 생성한다."""

    validate_fraction(sample_fraction, "sample_fraction")
    observed_at_value = observed_at or datetime.now(UTC) - timedelta(days=delay_days)
    query = _ranked_sample_query(source_paths)
    query = f"""
        WITH ranked AS ({query})
        SELECT
            * EXCLUDE (__sample_rank, __partition_count),
            ? AS observed_at
        FROM ranked
        WHERE __sample_rank <= greatest(
            1,
            CAST(ceil(__partition_count * ?) AS BIGINT)
        )
    """
    return write_case_file(
        connection=connection,
        case_name="freshness_delay",
        output_root=output_root,
        query=query,
        params=[
            *source_paths_parameter(source_paths),
            observed_at_value,
            sample_fraction,
        ],
    )


def validate_fraction(value: float, name: str) -> None:
    """비율 인자가 0보다 크고 1 이하인지 검증한다."""

    if not 0 < value <= 1:
        msg = f"{name}은 0보다 크고 1 이하이어야 합니다: {value}"
        raise SyntheticCaseError(msg)


def _ranked_sample_query(source_paths: Sequence[str | Path]) -> str:
    """연도별 안정적 샘플 순위를 붙인 원천 조회 SQL을 만든다."""

    source_query = source_union_sql(source_paths)
    return f"""
        SELECT
            *,
            row_number() OVER (
                PARTITION BY activity_year
                ORDER BY
                    activity_year,
                    state_code,
                    county_code,
                    loan_purpose,
                    action_taken,
                    loan_amount,
                    income
            ) AS __sample_rank,
            count(*) OVER (PARTITION BY activity_year) AS __partition_count
        FROM ({source_query})
    """
