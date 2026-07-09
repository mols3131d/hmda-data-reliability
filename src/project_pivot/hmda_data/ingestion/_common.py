"""HMDA 적재 내부 공통 헬퍼."""

from __future__ import annotations

from collections.abc import Iterable

import duckdb

from project_pivot.data_platform.duckdb import table_columns
from project_pivot.hmda_data.errors import HMDADataValidationError
from project_pivot.logger import get_logger

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
_LOGGER = get_logger("project_pivot.hmda_data.ingestion")


def validate_required_columns(
    connection: duckdb.DuckDBPyConnection,
    table_name: str = HMDA_LOANS_TABLE,
    required_columns: Iterable[str] = REQUIRED_HMDA_COLUMNS,
) -> None:
    """HMDA 핵심 컬럼 존재 여부를 검증한다."""

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
