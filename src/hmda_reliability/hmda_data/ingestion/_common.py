"""HMDA ingestion이 공유하는 Bronze schema contract와 validation."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

import duckdb

from hmda_reliability.data_platform.duckdb import table_columns
from hmda_reliability.hmda_data.errors import HMDADataValidationError
from hmda_reliability.hmda_data.ingestion._source_query import source_union_sql
from hmda_reliability.logger import get_logger

HMDA_LOANS_TABLE = "raw.hmda_loans"
REQUIRED_HMDA_COLUMNS = frozenset(
    {
        "activity_year",
        "loan_purpose",
        "action_taken",
        "loan_amount",
        "income",
        "state_code",
        "county_code",
    }
)
_LOGGER = get_logger("hmda_reliability.hmda_data.ingestion")


def validate_source_required_columns(
    connection: duckdb.DuckDBPyConnection,
    source_paths: Sequence[Path],
) -> None:
    """결합 결과의 NULL padding에 가려질 수 있는 개별 원천의 필수 컬럼을 검증한다.

    적재와 같은 reader로 검사하며 컬럼 type이나 실제 NULL 값은 거부하지 않는다.
    """

    for path in source_paths:
        rows = connection.execute(
            f"DESCRIBE {source_union_sql([path])}",
            [path.as_posix()],
        ).fetchall()
        actual_columns = {str(row[0]) for row in rows}
        missing_columns = sorted(REQUIRED_HMDA_COLUMNS - actual_columns)
        if missing_columns:
            context = {
                "source_path": path.as_posix(),
                "missing_columns": missing_columns,
                "actual_column_count": len(actual_columns),
            }
            _LOGGER.error("HMDA 원천 파일 핵심 컬럼 누락", extra=context)
            msg = "HMDA 원천 파일에 필수 컬럼이 없습니다."
            raise HMDADataValidationError(msg, context=context)


def validate_required_columns(
    connection: duckdb.DuckDBPyConnection,
    table_name: str = HMDA_LOANS_TABLE,
    required_columns: Iterable[str] = REQUIRED_HMDA_COLUMNS,
) -> None:
    """Required column set의 존재만 확인한다.

    Column type이나 row value는 검증하지 않는다. 누락된 컬럼은
    ``HMDADataValidationError``로 노출한다.
    """

    actual_columns = table_columns(connection, table_name)
    expected_columns = set(required_columns)
    missing_columns = sorted(expected_columns - actual_columns)
    if missing_columns:
        context = {
            "table_name": table_name,
            "missing_columns": missing_columns,
            "actual_column_count": len(actual_columns),
        }
        _LOGGER.error("HMDA 핵심 컬럼 누락", extra=context)
        msg = "HMDA 원천 데이터에 필수 컬럼이 없습니다."
        raise HMDADataValidationError(msg, context=context)
