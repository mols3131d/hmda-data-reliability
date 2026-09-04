"""Reliability 평가 입력으로 사용할 HMDA synthetic defect cases."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import duckdb

from hmda_reliability.data_platform.sql import quote_identifier
from hmda_reliability.hmda_data.errors import SyntheticCaseError
from hmda_reliability.hmda_data.synthetic._source import (
    require_columns,
    source_paths_parameter,
    source_union_sql,
)
from hmda_reliability.hmda_data.synthetic._writer import write_case_file


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
    case_name: str | None = None,
    target_year: int | None = None,
) -> Path:
    """Sampled non-null ``target_column`` 값을 결정적으로 Null로 만든다.

    결과 null rate는 source보다 항상 커야 한다. 각 fraction은 ``0 < value <= 1``이어야
    하고 target column이 없거나 모든 값이 이미 Null이면 ``SyntheticCaseError``를
    발생시킨다.

    ``target_year``가 지정되면 결과의 ``activity_year``를 해당 연도로 교체한다.
    ``target_year``는 2000 이상 2100 이하의 정수여야 하며(``bool`` 제외),
    ``target_column``이 ``activity_year``인 경우 상호 모순으로 거부된다. 또한
    원천 데이터가 둘 이상의 서로 다른 ``activity_year``를 포함하면 파티션 왜곡을
    방지하기 위해 거부된다.
    ``case_name``을 직접 지정할 때 ``target_year``가 주어지면 파티션 인제스션
    호환성을 위해 ``case_name``에 지정된 ``target_year``가 포함되어 있어야 한다.
    ``case_name``을 생략하면 ``target_year`` 지정 시 ``null_spike_{target_year}``,
    미지정 시 ``null_spike``를 사용한다. Source file은 수정하지 않는다.
    """

    _validate_fraction(null_fraction, "null_fraction")
    _validate_fraction(sample_fraction, "sample_fraction")
    if target_year is not None:
        if (
            not isinstance(target_year, int)
            or isinstance(target_year, bool)
            or not (2000 <= target_year <= 2100)
        ):
            msg = f"target_year는 2000 이상 2100 이하의 정수여야 합니다: {target_year}"
            raise SyntheticCaseError(msg, context={"target_year": target_year})
        if target_column == "activity_year":
            msg = (
                "target_year와 target_column='activity_year'는 "
                "동시에 지정할 수 없습니다."
            )
            raise SyntheticCaseError(
                msg,
                context={"target_column": target_column, "target_year": target_year},
            )
        if case_name is not None and str(target_year) not in case_name:
            msg = (
                f"target_year({target_year})가 지정된 경우 case_name에 해당 연도가 "
                f"포함되어야 합니다: {case_name}"
            )
            raise SyntheticCaseError(
                msg,
                context={"case_name": case_name, "target_year": target_year},
            )

    require_columns(connection, source_paths, {target_column, "activity_year"})
    quoted_target = quote_identifier(target_column)
    source_query = source_union_sql(source_paths)
    source_params = source_paths_parameter(source_paths)

    if target_year is not None:
        try:
            year_query = (
                f"SELECT count(*) FROM (SELECT DISTINCT activity_year "
                f"FROM ({source_query}))"
            )
            distinct_year_rows = connection.execute(
                year_query,
                source_params,
            ).fetchone()
        except duckdb.Error as exc:
            msg = "HMDA 합성 원천 연도 통계 조회에 실패했습니다."
            raise SyntheticCaseError(msg) from exc
        if distinct_year_rows and distinct_year_rows[0] > 1:
            msg = "target_year는 단일 연도 원천 데이터에 대해서만 지정할 수 있습니다."
            raise SyntheticCaseError(
                msg,
                context={
                    "distinct_years": int(distinct_year_rows[0]),
                    "target_year": target_year,
                },
            )

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
    if sample_non_null_count == 0:
        msg = "null_spike target_column에 non-null 값이 없어 증가를 만들 수 없습니다."
        raise SyntheticCaseError(msg)
    source_null_count = source_count - source_non_null_count
    # Strict Null Rate 증가를 위한 연도별 대상 인덱스 계산 식:
    # 1) 요청된 null_fraction에 따른 최소 null 개수 (ceil)
    # 2) 원천 null 비율을 초과하기 위해 필요한 정수 단위 최소 null 개수
    null_threshold_expr = """
        least(
            __year_non_null,
            greatest(
                CAST(ceil(__year_count * ?) AS BIGINT),
                CAST(
                    (__year_count * CAST(? AS BIGINT))
                    // CAST(? AS BIGINT) AS BIGINT
                ) + 1 - (__year_count - __year_non_null)
            )
        )
    """
    year_override_sql = (
        ", CAST(? AS INTEGER) AS activity_year" if target_year is not None else ""
    )
    case_query = f"""
        WITH sampled AS ({sampled_query}),
        year_stats AS (
            SELECT
                *,
                count(*) OVER (PARTITION BY activity_year)
                    AS __year_count,
                count({quoted_target}) OVER (PARTITION BY activity_year)
                    AS __year_non_null,
                row_number() OVER (
                    PARTITION BY activity_year
                    ORDER BY
                        CASE WHEN {quoted_target} IS NULL THEN 1 ELSE 0 END,
                        __sample_rank
                ) AS __non_null_rank
            FROM sampled
        )
        SELECT
            * EXCLUDE (
                __sample_rank,
                __partition_count,
                __null_sample_rank,
                __non_null_rank,
                __year_count,
                __year_non_null
            )
            REPLACE (
                CASE
                    WHEN {quoted_target} IS NOT NULL
                    AND __non_null_rank <= {null_threshold_expr}
                    THEN NULL
                    ELSE {quoted_target}
                END AS {quoted_target}
                {year_override_sql}
            )
        FROM year_stats
    """
    params: list[object] = [
        *source_params,
        sample_fraction,
        null_fraction,
        source_null_count,
        source_count,
    ]
    if target_year is not None:
        params.append(target_year)
    resolved_case_name = (
        case_name
        if case_name is not None
        else (f"null_spike_{target_year}" if target_year is not None else "null_spike")
    )
    return write_case_file(
        connection=connection,
        case_name=resolved_case_name,
        output_root=output_root,
        query=case_query,
        params=params,
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
    """합성 입력 관계에 대한 전체 row 수와 non-null 대상 컬럼 row 수를 조회한다."""

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


def _null_spike_sample_query(ranked_query: str, quoted_target: str) -> str:
    """연도별 샘플 카디널리티를 유지하면서 대상 값을 추출하는 쿼리를 생성한다."""

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
