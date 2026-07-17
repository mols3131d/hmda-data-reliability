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
    """원천 파일에서 raw.hmda_loans 스키마로 읽는 SELECT SQL을 만든다."""

    return f"""
        SELECT
            * EXCLUDE (filename),
            filename AS source_file,
            parse_filename(filename) AS source_file_name,
            TRY_CAST(
                regexp_extract(
                    parse_filename(filename, true),
                    '(\\d{{4}})',
                    1
                ) AS INTEGER
            )
                AS source_year,
            current_timestamp AS ingested_at
        FROM {_reader_sql(path)}
    """


def _reader_sql(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return """
            read_csv_auto(
                ?,
                header = true,
                nullstr = ['NA', ''],
                sample_size = 200000,
                filename = true
            )
        """
    if suffix == ".parquet":
        return "read_parquet(?, filename = true)"
    msg = f"지원하지 않는 HMDA 원천 파일 형식입니다: {path}"
    raise HMDADataLoadError(msg, context={"source_path": path.as_posix()})
