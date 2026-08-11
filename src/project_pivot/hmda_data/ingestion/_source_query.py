"""HMDA 원천 파일 reader SQL 생성."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from project_pivot.hmda_data.errors import HMDADataLoadError

HMDA_CSV_OPTIONS = {
    "header": True,
    "nullstr": ["NA", ""],
    "sample_size": 200_000,
}


def table_schema_name(table_name: str) -> str:
    """Qualified HMDA target의 schema를 반환하고 생략 시 raw를 사용한다."""

    parts = table_name.split(".")
    if len(parts) == 1:
        return "raw"
    if len(parts) == 2 and all(parts):
        return parts[0]
    msg = f"지원하지 않는 HMDA target table 이름입니다: {table_name}"
    raise HMDADataLoadError(msg, context={"table_name": table_name})


def csv_reader_sql(
    path_parameter: str = "?",
    *,
    include_filename: bool = True,
) -> str:
    """공유 HMDA CSV parse contract를 사용하는 DuckDB reader SQL을 반환한다."""

    filename_option = ",\n            filename = true" if include_filename else ""
    return f"""
        read_csv_auto(
            {path_parameter},
            header = {str(HMDA_CSV_OPTIONS["header"]).lower()},
            nullstr = {HMDA_CSV_OPTIONS["nullstr"]!r},
            sample_size = {HMDA_CSV_OPTIONS["sample_size"]}{filename_option}
        )
    """


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


def source_union_sql(
    source_paths: Sequence[Path],
    *,
    preserve_source_metadata: bool = False,
) -> str:
    """여러 원천 파일을 이름 기준 UNION하는 SQL을 만든다."""

    return "\nUNION ALL BY NAME\n".join(
        _source_select_sql(path, preserve_source_metadata=preserve_source_metadata)
        for path in source_paths
    )


def _source_select_sql(path: Path, *, preserve_source_metadata: bool) -> str:
    """원천 파일을 읽고 파일 경로·이름·연도·적재 시각을 추가한다."""

    if preserve_source_metadata:
        return f"""
            SELECT
                * EXCLUDE (filename)
            FROM {_reader_sql(path)}
        """

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

    return csv_reader_sql()


def _parquet_reader_sql() -> str:
    """Parquet reader SQL을 반환한다."""

    return "read_parquet(?, filename = true)"
