"""Taxi 합성 원천 Parquet 검증."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import duckdb

from project_pivot.taxi_data.errors import SyntheticCaseError
from project_pivot.taxi_data.ingestion.partition import _source_paths_parameter


def source_parameter(source_paths: Sequence[str | Path]) -> str | list[str]:
    if not source_paths:
        msg = "합성 데이터 원천 Parquet 파일이 없습니다."
        raise SyntheticCaseError(msg)
    return _source_paths_parameter(source_paths)


def require_columns(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    required_columns: set[str],
) -> None:
    existing_columns = parquet_columns(connection, source_paths)
    missing_columns = sorted(required_columns.difference(existing_columns))
    if missing_columns:
        msg = f"원천 Parquet에 필요한 컬럼이 없습니다: {missing_columns}"
        raise SyntheticCaseError(msg)


def parquet_columns(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
) -> set[str]:
    try:
        rows = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?) LIMIT 0",
            [source_parameter(source_paths)],
        ).fetchall()
    except duckdb.Error as exc:
        msg = "원천 Parquet 스키마 조회에 실패했습니다."
        raise SyntheticCaseError(msg) from exc
    return {str(row[0]) for row in rows}
