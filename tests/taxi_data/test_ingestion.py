"""Taxi 원천 데이터 적재(Ingestion) 기능 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from project_pivot.taxi_data import (
    DuckDBConnectionManager,
    discover_yellow_tripdata_files,
    load_taxi_zones,
    load_yellow_tripdata,
)
from project_pivot.taxi_data.errors import TaxiDataLoadError


def test_raw_loaders_are_idempotent(
    zone_csv_path: Path,
    tripdata_parquet_path: Path,
) -> None:
    """CSV/Parquet 원천 적재가 중복 없이 테이블을 재생성하는지 검증한다."""
    with DuckDBConnectionManager() as connection:
        assert load_taxi_zones(connection, zone_csv_path) == 2
        assert load_taxi_zones(connection, zone_csv_path) == 2
        assert load_yellow_tripdata(connection, [tripdata_parquet_path]) == 16
        assert load_yellow_tripdata(connection, [tripdata_parquet_path]) == 16

        zones_count = connection.execute(
            "SELECT count(*) FROM raw.taxi_zones"
        ).fetchone()
        tripdata_stats = connection.execute(
            """
            SELECT count(*), min(source_partition), max(source_partition)
            FROM raw.yellow_tripdata
            """
        ).fetchone()

    assert zones_count is not None
    assert tripdata_stats is not None
    assert zones_count == (2,)
    assert tripdata_stats == (16, "2024-01", "2024-01")


def test_raw_loader_wraps_duckdb_errors(tmp_path: Path) -> None:
    """원천 파일 오류가 적재 도메인 예외로 변환되는지 검증한다."""
    missing_csv_path = tmp_path / "missing.csv"

    with (
        DuckDBConnectionManager() as connection,
        pytest.raises(TaxiDataLoadError, match="택시 존 CSV 적재"),
    ):
        load_taxi_zones(connection, missing_csv_path)


def test_discover_yellow_tripdata_files_filters_monthly_files_by_year(
    tmp_path: Path,
) -> None:
    """지정 연도의 월별 원천 파일만 정렬해 찾는다."""

    expected_paths = [
        tmp_path / "yellow_tripdata_2025-01.parquet",
        tmp_path / "yellow_tripdata_2025-02.parquet",
    ]
    extra_paths = [
        tmp_path / "yellow_tripdata_2024-12.parquet",
        tmp_path / "yellow_tripdata_2025-01-refresh.parquet",
        tmp_path / "yellow_tripdata_2025-invalid.parquet",
    ]
    for path in [*expected_paths, *extra_paths]:
        path.touch()

    assert discover_yellow_tripdata_files(tmp_path, year=2025) == expected_paths


def test_discover_yellow_tripdata_files_rejects_missing_directory(
    tmp_path: Path,
) -> None:
    """없는 원천 디렉터리는 명확한 적재 예외로 실패한다."""

    with pytest.raises(TaxiDataLoadError, match="원천 디렉터리"):
        discover_yellow_tripdata_files(tmp_path / "missing", year=2025)
