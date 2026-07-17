"""HMDA 원천 파일 reader SQL 생성."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from project_pivot.hmda_data.errors import HMDADataLoadError


def validate_source_paths(source_paths: Sequence[str | Path]) -> list[Path]:
    """HMDA 원천 파일 경로를 검증하고 Path 목록으로 반환한다."""

    if not source_paths:
        raise HMDADataLoadError(message="적재할 HMDA CSV 또는 Parquet 파일이 없습니다.")

    paths = [Path(path) for path in source_paths]
    unsupported_paths = [
        path.as_posix()
        for path in paths
        if path.suffix.lower() not in {".csv", ".parquet"}
    ]
    if unsupported_paths:
        raise HMDADataLoadError(
            message="지원하지 않는 HMDA 원천 파일 형식입니다.",
            context={"unsupported_paths": unsupported_paths},
        )
    return paths


def source_union_sql(source_paths: Sequence[Path]) -> str:
    """여러 원천 파일을 이름 기준 UNION하는 SQL을 만든다."""

    return "\nUNION ALL BY NAME\n".join(
        _source_select_sql(path) for path in source_paths
    )


def _source_select_sql(path: Path) -> str:
    """원천 파일을 읽고 파일 경로·이름·연도·적재 시각을 추가한다."""

    return f"""
        SELECT
            * EXCLUDE (filename),
            filename AS source_file,
            parse_filename(filename) AS source_file_name,
            {_source_year_sql()} AS source_year,
            current_timestamp AS ingested_at
        FROM {_reader_sql(path)}
    """


def _source_year_sql() -> str:
    """파일명에서 네 자리 연도를 추출하는 SQL을 반환한다."""

    return """
        TRY_CAST(
            regexp_extract(parse_filename(filename), '(\\d{4})', 1)
            AS INTEGER
        )
    """


def _reader_sql(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _csv_reader_sql()
    if suffix == ".parquet":
        return _parquet_reader_sql()
    msg = f"지원하지 않는 HMDA 원천 파일 형식입니다: {path}"
    raise HMDADataLoadError(msg, context={"source_path": path.as_posix()})


def _csv_reader_sql() -> str:
    """CSV reader SQL을 반환한다."""

    return """
        read_csv_auto(
            ?,
            header = true,
            nullstr = ['NA', ''],
            sample_size = 200000,
            filename = true
        )
    """


def _parquet_reader_sql() -> str:
    """Parquet reader SQL을 반환한다."""

    return "read_parquet(?, filename = true)"
