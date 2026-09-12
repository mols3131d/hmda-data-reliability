"""Data Operations 품질 게이트 실행 경계."""

from __future__ import annotations

from datetime import UTC, datetime

import duckdb

from hmda_reliability.data_operations.request import DataOperationRequest
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.data_platform.sql import qualify_table_name, quote_identifier
from hmda_reliability.hmda_data import HMDA_LOANS_TABLE
from hmda_reliability.reliability import (
    ProfileSnapshotRequest,
    create_profile_snapshot,
    evaluate_profile_quality_gate,
    reject_missing_partition_discriminator,
)

_DBT_SOURCE_PARTITION_COLUMN = "activity_year"


def evaluate_quality_gate(request: DataOperationRequest) -> None:
    """dbt source가 소비할 전체 Bronze 파티션에 Reliability 정책을 적용한다.

    검증 실패 시 `QualityGateError`가 발생하며 downstream dbt build를 중단해야 한다.
    `request.raw_table_name`과 `request.partition_column`이 canonical contract
    (`raw.hmda_loans`, `activity_year`)와 일치하지 않으면 `ValueError`를 발생시킨다.
    """

    _validate_dbt_source_contract(request)
    observed_at = request.observed_at or datetime.now(UTC)
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        partitions = _bronze_partitions(connection, request)
        for partition in partitions:
            current = create_profile_snapshot(
                connection,
                ProfileSnapshotRequest(
                    asset_name=request.asset_name,
                    table_name=request.raw_table_name,
                    partition_column=request.partition_column,
                    partition=partition,
                    profile_columns=request.profile_columns,
                    observed_at=observed_at,
                ),
            )
            evaluate_profile_quality_gate(current)


def _bronze_partitions(
    connection: duckdb.DuckDBPyConnection,
    request: DataOperationRequest,
) -> tuple[str, ...]:
    """Bronze 테이블에 존재하는 파티션 목록과 request.source_year를 정렬 반환한다.

    파티션 컬럼(`activity_year`)이 NULL인 행이 하나라도 존재하면 조기에
    `reject_missing_partition_discriminator()`를 통해 차단한다.
    """
    missing_partition_count = connection.execute(
        f"""
        SELECT count(*)
        FROM {qualify_table_name(request.raw_table_name)}
        WHERE {quote_identifier(request.partition_column)} IS NULL
        """
    ).fetchone()
    if missing_partition_count and int(missing_partition_count[0]) > 0:
        reject_missing_partition_discriminator(
            asset_name=request.asset_name,
            row_count=int(missing_partition_count[0]),
        )

    rows = connection.execute(
        f"""
        SELECT DISTINCT CAST({quote_identifier(request.partition_column)} AS VARCHAR)
        FROM {qualify_table_name(request.raw_table_name)}
        WHERE {quote_identifier(request.partition_column)} IS NOT NULL
        ORDER BY 1
        """
    ).fetchall()
    partitions = {str(row[0]) for row in rows}
    partitions.add(str(request.source_year))
    return tuple(sorted(partitions))


def _validate_dbt_source_contract(request: DataOperationRequest) -> None:
    """테이블과 파티션 컬럼이 dbt canonical 소스 규약과 일치하는지 검증한다."""
    if (
        request.raw_table_name != HMDA_LOANS_TABLE
        or request.partition_column != _DBT_SOURCE_PARTITION_COLUMN
    ):
        message = (
            "quality gate request는 canonical dbt source를 사용해야 합니다: "
            f"table={HMDA_LOANS_TABLE}, "
            f"partition_column={_DBT_SOURCE_PARTITION_COLUMN}"
        )
        raise ValueError(message)
