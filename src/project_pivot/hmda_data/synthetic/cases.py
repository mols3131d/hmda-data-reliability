"""Reliability 평가 입력으로 사용할 HMDA synthetic defect cases."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb

from project_pivot.data_platform.sql import quote_identifier
from project_pivot.hmda_data.errors import SyntheticCaseError
from project_pivot.hmda_data.synthetic._source import (
    require_columns,
    source_paths_parameter,
    source_union_sql,
)
from project_pivot.hmda_data.synthetic._writer import write_case_file


def row_count_drop(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    output_root: str | Path,
    *,
    sample_fraction: float = 0.1,
) -> Path:
    """각 ``activity_year`` partition에 같은 fraction을 적용한 row-count drop을 만든다.

    연도별 최소 한 row는 남긴다. ``sample_fraction``은 ``0 < value <= 1``이어야 하며
    source file은 수정하지 않는다.
    """

    _validate_fraction(sample_fraction, "sample_fraction")
    ranked_query = _ranked_sample_query(connection, source_paths)
    case_query = f"""
        WITH ranked AS ({ranked_query})
        SELECT * EXCLUDE (__sample_rank, __partition_count)
        FROM ranked
        WHERE {_sample_limit_sql()}
    """
    return write_case_file(
        connection=connection,
        case_name="row_count_drop",
        output_root=output_root,
        query=case_query,
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
    """연도별 sampled rows의 일부 ``target_column`` 값을 Null로 만든다.

    각 연도에서 최소 ``null_fraction``에 해당하는 sampled row를 Null로 만들며 기존 Null은
    그대로 남는다. 각 fraction은 ``0 < value <= 1``이어야 하고 target column이 없으면
    ``SyntheticCaseError``를 발생시킨다. Source file은 수정하지 않는다.
    """

    _validate_fraction(null_fraction, "null_fraction")
    _validate_fraction(sample_fraction, "sample_fraction")
    require_columns(connection, source_paths, {target_column})
    quoted_target = quote_identifier(target_column)
    ranked_query = _ranked_sample_query(connection, source_paths)
    case_query = f"""
        WITH ranked AS ({ranked_query}),
        sampled AS (
            SELECT *
            FROM ranked
            WHERE {_sample_limit_sql()}
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
                    ELSE {quoted_target}
                END AS {quoted_target}
            )
        FROM null_ranked
    """
    return write_case_file(
        connection=connection,
        case_name="null_spike",
        output_root=output_root,
        query=case_query,
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
    """Sampled rows의 ``target_column``을 ``VARCHAR``로 cast한 case를 만든다.

    ``sample_fraction``은 ``0 < value <= 1``이어야 하고 target column이 없으면
    ``SyntheticCaseError``를 발생시킨다. Source file은 수정하지 않는다.
    """

    _validate_fraction(sample_fraction, "sample_fraction")
    require_columns(connection, source_paths, {target_column})
    quoted_target = quote_identifier(target_column)
    ranked_query = _ranked_sample_query(connection, source_paths)
    case_query = f"""
        WITH ranked AS ({ranked_query})
        SELECT
            * EXCLUDE (__sample_rank, __partition_count)
            REPLACE (CAST({quoted_target} AS VARCHAR) AS {quoted_target})
        FROM ranked
        WHERE {_sample_limit_sql()}
    """
    return write_case_file(
        connection=connection,
        case_name="schema_drift",
        output_root=output_root,
        query=case_query,
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
    """Sampled rows에 하나의 ``observed_at`` 값을 추가한 freshness case를 만든다.

    ``observed_at``을 주면 그 값을 그대로 사용하고 ``delay_days``는 적용하지 않는다.
    생략하면 현재 UTC 시각에서 ``delay_days``를 뺀 값을 사용한다. ``sample_fraction``은
    ``0 < value <= 1``이어야 하며 source file은 수정하지 않는다.
    """

    _validate_fraction(sample_fraction, "sample_fraction")
    delayed_observed_at = observed_at or datetime.now(UTC) - timedelta(days=delay_days)
    ranked_query = _ranked_sample_query(connection, source_paths)
    case_query = f"""
        WITH ranked AS ({ranked_query})
        SELECT
            * EXCLUDE (__sample_rank, __partition_count),
            ? AS observed_at
        FROM ranked
        WHERE {_sample_limit_sql()}
    """
    return write_case_file(
        connection=connection,
        case_name="freshness_delay",
        output_root=output_root,
        query=case_query,
        params=[
            *source_paths_parameter(source_paths),
            delayed_observed_at,
            sample_fraction,
        ],
    )


def _validate_fraction(value: float, name: str) -> None:
    """비율 인자가 0보다 크고 1 이하인지 검증한다."""

    if not 0 < value <= 1:
        msg = f"{name}은 0보다 크고 1 이하이어야 합니다: {value}"
        raise SyntheticCaseError(msg)


def _sample_limit_sql() -> str:
    """각 연도 partition에 최소 한 row를 남기는 sample limit을 만든다."""

    return """
        __sample_rank <= greatest(
            1,
            CAST(ceil(__partition_count * ?) AS BIGINT)
        )
    """


def _ranked_sample_query(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
) -> str:
    """연도별 stable sample rank를 만든다."""

    source_query = source_union_sql(source_paths)
    try:
        # Canonical column order로 만든 row hash는 source column order에 영향받지 않는다.
        columns = sorted(
            str(row[0])
            for row in connection.execute(
                f"DESCRIBE SELECT * FROM ({source_query}) LIMIT 0",
                source_paths_parameter(source_paths),
            ).fetchall()
            if str(row[0]) != "ingested_at"
        )
    except duckdb.Error as exc:
        raise SyntheticCaseError("HMDA 합성 원천 스키마 조회에 실패했습니다.") from exc
    packed_columns = ", ".join(
        f"{quote_identifier(column)} := {quote_identifier(column)}"
        for column in columns
    )
    return f"""
        SELECT
            *,
            row_number() OVER (
                PARTITION BY activity_year
                ORDER BY
                    md5(to_json(struct_pack({packed_columns})))
            ) AS __sample_rank,
            count(*) OVER (PARTITION BY activity_year) AS __partition_count
        FROM ({source_query})
    """
