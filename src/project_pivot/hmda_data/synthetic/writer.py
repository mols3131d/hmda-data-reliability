"""HMDA 합성 결함 파일 쓰기."""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb

from project_pivot.data_platform.sql import quote_string_literal
from project_pivot.hmda_data.errors import SyntheticCaseError
from project_pivot.logger import get_logger

LOGGER = get_logger(__name__)


def write_case_file(
    *,
    connection: duckdb.DuckDBPyConnection,
    case_name: str,
    output_root: str | Path,
    query: str,
    params: list[object],
) -> Path:
    """합성 결함 케이스를 단일 Parquet 파일로 쓴다."""

    case_dir = prepare_case_dir(output_root, case_name)
    target_path = case_dir / f"{case_name}.parquet"
    try:
        connection.execute(
            f"""
            COPY ({query})
            TO {quote_string_literal(str(target_path))}
            (FORMAT PARQUET)
            """,
            params,
        )
    except duckdb.Error as exc:
        msg = (
            "HMDA 합성 결함 파일 생성에 실패했습니다: "
            f"case={case_name}, output_root={output_root}"
        )
        raise SyntheticCaseError(msg, context={"case_name": case_name}) from exc
    LOGGER.debug(
        "HMDA 합성 결함 파일 생성 완료",
        extra={"case_name": case_name, "target_path": str(target_path)},
    )
    return target_path


def prepare_case_dir(output_root: str | Path, case_name: str) -> Path:
    """케이스 출력 디렉터리를 비우고 다시 생성한다."""

    case_dir = Path(output_root) / case_name
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir
