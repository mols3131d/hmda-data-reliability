"""HMDA 합성 원천 파일 검증."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import duckdb

from project_pivot.hmda_data.errors import SyntheticCaseError


def source_paths_parameter(source_paths: Sequence[str | Path]) -> list[str]:
    """합성 케이스 원천 파일 경로를 DuckDB 파라미터로 정규화한다."""

    if not source_paths:
        raise SyntheticCaseError("HMDA 합성 데이터 원천 파일이 없습니다.")
    paths = [Path(path) for path in source_paths]
    unsupported_paths = [
        path.as_posix()
        for path in paths
        if path.suffix.lower() not in {".csv", ".parquet"}
    ]
    if unsupported_paths:
        raise SyntheticCaseError(
            "지원하지 않는 HMDA 합성 원천 파일 형식입니다.",
            context={"unsupported_paths": unsupported_paths},
        )
    return [path.as_posix() for path in paths]


def require_columns(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
    required_columns: set[str],
) -> None:
    """원천 파일에 필요한 컬럼이 모두 있는지 검증한다."""

    existing_columns = _source_columns(connection, source_paths)
    missing_columns = sorted(required_columns.difference(existing_columns))
    if missing_columns:
        msg = f"HMDA 원천 파일에 필요한 컬럼이 없습니다: {missing_columns}"
        raise SyntheticCaseError(msg, context={"missing_columns": missing_columns})


def _source_columns(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
) -> set[str]:
    """원천 CSV/Parquet 파일의 컬럼명을 조회한다."""

    try:
        rows = connection.execute(
            f"DESCRIBE SELECT * FROM ({source_union_sql(source_paths)}) LIMIT 0",
            source_paths_parameter(source_paths),
        ).fetchall()
    except duckdb.Error as exc:
        msg = "HMDA 합성 원천 스키마 조회에 실패했습니다."
        raise SyntheticCaseError(msg) from exc
    return {str(row[0]) for row in rows}


def source_union_sql(source_paths: Sequence[str | Path]) -> str:
    """여러 원천 파일을 이름 기준 UNION ALL 하는 SQL을 만든다."""

    paths = [Path(path) for path in source_paths]
    selects = [_reader_sql(path) for path in paths]
    return "\nUNION ALL BY NAME\n".join(selects)


def _reader_sql(path: Path) -> str:
    """파일 확장자에 맞는 DuckDB reader SQL을 반환한다."""

    if path.suffix.lower() == ".csv":
        return """
            SELECT *
            FROM read_csv_auto(
                ?,
                header = true,
                nullstr = ['NA', ''],
                sample_size = 200000
            )
        """
    if path.suffix.lower() == ".parquet":
        return "SELECT * FROM read_parquet(?)"
    msg = f"지원하지 않는 HMDA 합성 원천 파일 형식입니다: {path}"
    raise SyntheticCaseError(msg, context={"source_path": path.as_posix()})
