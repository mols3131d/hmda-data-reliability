"""HMDA 연도/파일 파티션 적재 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import load_hmda_loans_partition
from project_pivot.hmda_data.errors import HMDADataLoadError

pytestmark = pytest.mark.component


def test_load_hmda_loans_partition_filters_by_source_year(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    """source_year 기준으로 특정 연도 파일만 적재한다."""

    with DuckDBConnectionManager() as connection:
        row_count = load_hmda_loans_partition(
            connection,
            [hmda_csv_path, hmda_parquet_path],
            2025,
        )
        stats = connection.execute(
            """
            SELECT count(*), min(activity_year), max(activity_year), min(source_year)
            FROM raw.hmda_loans
            """
        ).fetchone()

    assert row_count == 2
    assert stats == (2, 2025, 2025, 2025)


def test_load_hmda_loans_partition_is_idempotent(
    hmda_csv_path: Path,
) -> None:
    """동일 source_year 재적재 시 중복 없이 덮어쓴다."""

    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2
        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2

        row = connection.execute("SELECT count(*) FROM raw.hmda_loans").fetchone()

    assert row == (2,)


def test_partition_load_creates_custom_target_schema(hmda_csv_path: Path) -> None:
    """파티션 적재는 configured qualified target의 schema를 새 DB에 생성한다."""

    with DuckDBConnectionManager() as connection:
        row_count = load_hmda_loans_partition(
            connection,
            [hmda_csv_path],
            2025,
            table_name="bronze.hmda_loans",
        )
        table = connection.execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = 'bronze' AND table_name = 'hmda_loans'
            """
        ).fetchone()

    assert row_count == 2
    assert table == ("bronze", "hmda_loans")


def test_partition_load_rejects_multipart_target_table(hmda_csv_path: Path) -> None:
    """현재 loader contract 밖의 multipart target은 schema 생성 전에 거부한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(HMDADataLoadError, match="target table"),
    ):
        load_hmda_loans_partition(
            connection,
            [hmda_csv_path],
            2025,
            table_name="catalog.bronze.hmda_loans",
        )


def test_load_hmda_loans_partition_filters_by_source_file(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    """source_file이 지정되면 해당 파일만 적재한다."""

    with DuckDBConnectionManager() as connection:
        row_count = load_hmda_loans_partition(
            connection,
            [hmda_csv_path, hmda_parquet_path],
            2024,
            source_file=hmda_parquet_path.name,
        )
        source_files = connection.execute(
            """
            SELECT DISTINCT source_file_name
            FROM raw.hmda_loans
            """
        ).fetchall()

    assert row_count == 1
    assert source_files == [(hmda_parquet_path.name,)]


def test_load_hmda_loans_partition_preserves_outlier_rows(tmp_path: Path) -> None:
    """비정상 HMDA 값도 품질 감지 evidence를 위해 보존한다."""

    path = tmp_path / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,99,999999999999,-10,ZZ,99999",
            ]
        ),
        encoding="utf-8",
    )

    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans_partition(connection, [path], 2025) == 1
        row = connection.execute(
            """
            SELECT action_taken, loan_amount, income, state_code, county_code
            FROM raw.hmda_loans
            """
        ).fetchone()

    assert row == (99, 999999999999, -10, "ZZ", 99999)


def test_load_hmda_loans_partition_handles_empty_source_file(
    hmda_csv_path: Path,
) -> None:
    """빈 source_file도 SQL binding 오류 대신 도메인 오류로 반환한다."""

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(HMDADataLoadError, match="적재할 행이 없습니다"),
    ):
        load_hmda_loans_partition(
            connection,
            [hmda_csv_path],
            2025,
            source_file="",
        )
