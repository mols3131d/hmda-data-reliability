"""Reliability 평가 입력으로 사용할 HMDA synthetic defect cases."""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil
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
    """Sampled non-null ``target_column`` 값을 결정적으로 Null로 만든다.

    결과 null rate는 source보다 항상 커야 한다. 각 fraction은 ``0 < value <= 1``이어야
    하고 target column이 없거나 모든 값이 이미 Null이면 ``SyntheticCaseError``를
    발생시킨다. Source file은 수정하지 않는다.
    """

    _validate_fraction(null_fraction, "null_fraction")
    _validate_fraction(sample_fraction, "sample_fraction")
    require_columns(connection, source_paths, {target_column})
    quoted_target = quote_identifier(target_column)
    source_query = source_union_sql(source_paths)
    source_params = source_paths_parameter(source_paths)
    source_count, source_non_null_count = _target_value_counts(
        connection,
        query=source_query,
        params=source_params,
        quoted_target=quoted_target,
    )
    if source_non_null_count == 0:
        msg = "null_spike target_column에 non-null 값이 없어 증가를 만들 수 없습니다."
        raise SyntheticCaseError(msg)

    ranked_query = _ranked_sample_query(connection, source_paths)
    sampled_query = _null_spike_sample_query(ranked_query, quoted_target)
    sample_count, sample_non_null_count = _target_value_counts(
        connection,
        query=sampled_query,
        params=[*source_params, sample_fraction],
        quoted_target=quoted_target,
    )
    mutation_count = _null_spike_mutation_count(
        source_count=source_count,
        source_non_null_count=source_non_null_count,
        sample_count=sample_count,
        sample_non_null_count=sample_non_null_count,
        null_fraction=null_fraction,
    )
    case_query = f"""
        WITH sampled AS ({sampled_query}),
        null_ranked AS (
            SELECT
                *,
                row_number() OVER (
                    ORDER BY
                        CASE WHEN {quoted_target} IS NULL THEN 1 ELSE 0 END,
                        activity_year,
                        __sample_rank
                ) AS __non_null_rank
            FROM sampled
        )
        SELECT
            * EXCLUDE (
                __sample_rank,
                __partition_count,
                __null_sample_rank,
                __non_null_rank
            )
            REPLACE (
                CASE
                    WHEN {quoted_target} IS NOT NULL
                    AND __non_null_rank <= ?
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
        params=[*source_params, sample_fraction, mutation_count],
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


def _validate_fraction(value: float, name: str) -> None:
    """비율 인자가 0보다 크고 1 이하인지 검증한다."""

    if not 0 < value <= 1:
        msg = f"{name}은 0보다 크고 1 이하이어야 합니다: {value}"
        raise SyntheticCaseError(msg)


def _target_value_counts(
    connection: duckdb.DuckDBPyConnection,
    *,
    query: str,
    params: Sequence[object],
    quoted_target: str,
) -> tuple[int, int]:
    """Query row and non-null target counts for a synthetic input relation."""

    try:
        row = connection.execute(
            f"""
            SELECT count(*), count({quoted_target})
            FROM ({query})
            """,
            params,
        ).fetchone()
    except duckdb.Error as exc:
        msg = "HMDA 합성 null_spike 통계 조회에 실패했습니다."
        raise SyntheticCaseError(msg) from exc
    if row is None:
        raise SyntheticCaseError("HMDA 합성 null_spike 통계가 없습니다.")
    return int(row[0]), int(row[1])


def _null_spike_mutation_count(
    *,
    source_count: int,
    source_non_null_count: int,
    sample_count: int,
    sample_non_null_count: int,
    null_fraction: float,
) -> int:
    """Return enough eligible mutations for a strict source-relative increase."""

    source_null_count = source_count - source_non_null_count
    sample_null_count = sample_count - sample_non_null_count
    minimum_output_null_count = source_null_count * sample_count // source_count + 1
    requested_mutation_count = max(1, ceil(sample_count * null_fraction))
    required_mutation_count = max(
        requested_mutation_count,
        minimum_output_null_count - sample_null_count,
    )
    return min(sample_non_null_count, required_mutation_count)


def _null_spike_sample_query(ranked_query: str, quoted_target: str) -> str:
    """Keep per-year sample cardinality while retaining eligible target values."""

    return f"""
        SELECT *
        FROM (
            SELECT
                *,
                row_number() OVER (
                    PARTITION BY activity_year
                    ORDER BY
                        CASE WHEN {quoted_target} IS NULL THEN 1 ELSE 0 END,
                        __sample_rank
                ) AS __null_sample_rank
            FROM ({ranked_query})
        )
        WHERE {_sample_limit_sql("__null_sample_rank")}
    """


def _sample_limit_sql(rank_column: str = "__sample_rank") -> str:
    """각 연도 partition에 최소 한 row를 남기는 sample limit을 만든다."""

    return f"""
        {rank_column} <= greatest(
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
        # Canonical column order의 row hash는 source column order에 영향받지 않는다.
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
