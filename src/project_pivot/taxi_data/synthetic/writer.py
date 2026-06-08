"""Taxi 합성 파티션 파일 쓰기."""

from __future__ import annotations

import shutil
from pathlib import Path

import duckdb

from project_pivot.logger import get_logger
from project_pivot.taxi_data.errors import SyntheticCaseError
from project_pivot.taxi_data.sql import quote_identifier, quote_string_literal

LOGGER = get_logger(__name__)


def write_partitioned_case(
    *,
    connection: duckdb.DuckDBPyConnection,
    case_name: str,
    output_root: str | Path,
    query: str,
    params: list[object],
    partition_column: str,
) -> Path:
    case_dir = prepare_case_dir(output_root, case_name)
    target_path = quote_string_literal(str(case_dir))
    try:
        connection.execute(
            f"""
            COPY ({query})
            TO {target_path}
            (FORMAT PARQUET, PARTITION_BY ({quote_identifier(partition_column)}))
            """,
            params,
        )
    except duckdb.Error as exc:
        msg = (
            "합성 결함 파티션 생성에 실패했습니다: "
            f"case={case_name}, output_root={output_root}, "
            f"partition_column={partition_column}"
        )
        raise SyntheticCaseError(msg) from exc
    LOGGER.debug(
        "합성 결함 파티션 생성 완료",
        extra={
            "case_name": case_name,
            "case_dir": str(case_dir),
            "partition_column": partition_column,
        },
    )
    return case_dir


def prepare_case_dir(output_root: str | Path, case_name: str) -> Path:
    case_dir = Path(output_root) / case_name
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir
