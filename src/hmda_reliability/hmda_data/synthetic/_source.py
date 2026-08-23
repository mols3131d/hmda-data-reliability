"""합성 결함 생성에 사용할 HMDA source set의 format과 schema를 검증한다."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import duckdb

from project_pivot.hmda_data.errors import SyntheticCaseError


def source_paths_parameter(source_paths: Sequence[str | Path]) -> list[str]:
    """빈 source set과 unsupported format을 거부하고 DuckDB path parameter를 만든다.

    파일 존재 여부와 parse 가능 여부는 실제 DuckDB read 단계에서 확인한다.
    """

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
    """Synthetic transformation에 필요한 source columns가 모두 존재하는지 확인한다."""

    existing_columns = _source_columns(connection, source_paths)
    missing_columns = sorted(required_columns.difference(existing_columns))
    if missing_columns:
        msg = f"HMDA 원천 파일에 필요한 컬럼이 없습니다: {missing_columns}"
        raise SyntheticCaseError(msg, context={"missing_columns": missing_columns})


def _source_columns(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[str | Path],
) -> set[str]:
    """실제 row materialization 없이 combined source schema를 조회한다."""

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
    """Source column order와 무관하게 파일들을 ``UNION ALL BY NAME``으로 결합한다."""

    paths = [Path(path) for path in source_paths]
    selects = [_reader_sql(path) for path in paths]
    return "\nUNION ALL BY NAME\n".join(selects)


def _reader_sql(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _csv_reader_sql()
    if suffix == ".parquet":
        return _parquet_reader_sql()
    msg = f"지원하지 않는 HMDA 합성 원천 파일 형식입니다: {path}"
    raise SyntheticCaseError(msg, context={"source_path": path.as_posix()})


def _csv_reader_sql() -> str:
    return """
        SELECT *
        FROM read_csv_auto(
            ?,
            header = true,
            nullstr = ['NA', ''],
            sample_size = 200000
        )
    """


def _parquet_reader_sql() -> str:
    return "SELECT * FROM read_parquet(?)"
