"""HMDA 원천 데이터 적재 기능 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import (
    discover_hmda_files,
    load_hmda_loans,
    load_hmda_loans_partition,
)
from project_pivot.hmda_data.errors import HMDADataLoadError, HMDADataValidationError

pytestmark = pytest.mark.component


def test_discover_hmda_files_filters_supported_files(tmp_path: Path) -> None:
    """지원하는 CSV/Parquet 파일만 정렬해 찾는다."""

    expected_paths = [
        tmp_path / "hmda_2024.parquet",
        tmp_path / "year_2025.csv",
    ]
    ignored_paths = [
        tmp_path / "data_fields.html",
        tmp_path / "data_fields.md",
    ]
    for path in [*expected_paths, *ignored_paths]:
        path.touch()

    assert discover_hmda_files(tmp_path) == expected_paths


def test_discover_hmda_files_rejects_missing_directory(tmp_path: Path) -> None:
    """없는 원천 디렉터리는 명확한 적재 예외로 실패한다."""

    with pytest.raises(
        HMDADataLoadError,
        match="원천 디렉터리",
    ):
        discover_hmda_files(tmp_path / "missing")


def test_load_hmda_loans_loads_csv_and_parquet_idempotently(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    """CSV/Parquet 원천 적재가 중복 없이 테이블을 재생성하는지 검증한다."""

    source_paths = [hmda_csv_path, hmda_parquet_path]
    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans(connection, source_paths) == 3
        assert load_hmda_loans(connection, source_paths) == 3

        stats = connection.execute(
            """
            SELECT
                count(*),
                count(DISTINCT source_file),
                min(source_year),
                max(source_year),
                count(ingested_at)
            FROM raw.hmda_loans
            """
        ).fetchone()

    assert stats == (3, 2, 2024, 2025, 3)


def test_load_hmda_loans_partition_after_full_load(
    hmda_csv_path: Path,
    hmda_parquet_path: Path,
) -> None:
    """전체 적재 후 파티션 적재가 같은 raw 스키마를 공유하는지 검증한다."""

    with DuckDBConnectionManager() as connection:
        assert load_hmda_loans(connection, [hmda_parquet_path]) == 1
        assert load_hmda_loans_partition(connection, [hmda_csv_path], 2025) == 2

        stats = connection.execute(
            """
            SELECT
                count(*),
                count(DISTINCT source_file_name),
                min(source_year),
                max(source_year)
            FROM raw.hmda_loans
            """
        ).fetchone()

    assert stats == (3, 2, 2024, 2025)


def test_load_hmda_loans_wraps_duckdb_errors(tmp_path: Path) -> None:
    """원천 파일 오류가 HMDA 적재 예외로 변환되는지 검증한다."""

    missing_csv_path = tmp_path / "missing.csv"

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(
            HMDADataLoadError,
            match="HMDA 원천 데이터 적재",
        ),
    ):
        load_hmda_loans(connection, [missing_csv_path])


def test_load_hmda_loans_validates_required_columns(tmp_path: Path) -> None:
    """필수 컬럼 누락이 검증 예외로 드러나는지 확인한다."""

    path = tmp_path / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,state_code,county_code",
                "2025,1,1,350000,CA,06001",
            ]
        ),
        encoding="utf-8",
    )

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(
            HMDADataValidationError,
            match="필수 컬럼",
        ),
    ):
        load_hmda_loans(connection, [path])


def test_load_hmda_loans_rejects_malformed_csv_rows(tmp_path: Path) -> None:
    """손상된 CSV 행을 조용히 버리지 않고 적재 실패로 반환한다."""

    path = tmp_path / "malformed_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,1,1,350000,120,CA,06001,unexpected",
            ]
        ),
        encoding="utf-8",
    )

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises((HMDADataLoadError, HMDADataValidationError)),
    ):
        load_hmda_loans(connection, [path])
