"""Taxi 데이터 CLI 테스트."""

from __future__ import annotations

from pathlib import Path

from project_pivot.taxi_data import DuckDBConnectionManager
from project_pivot.taxi_data.cli import main


def test_load_raw_cli_populates_raw_tables(
    tmp_path: Path,
    zone_csv_path: Path,
    tripdata_parquet_path: Path,
) -> None:
    """load-raw 명령이 raw source table을 적재하는지 검증한다."""
    database_path = tmp_path / "project_pivot.duckdb"

    result = main(
        [
            "load-raw",
            "--database",
            str(database_path),
            "--source-root",
            str(tmp_path),
            "--zone-csv",
            str(zone_csv_path),
        ]
    )

    with DuckDBConnectionManager(database_path, read_only=True) as connection:
        row = connection.execute(
            """
            SELECT
                (SELECT count(*) FROM raw.taxi_zones),
                (SELECT count(*) FROM raw.yellow_tripdata)
            """
        ).fetchone()

    assert result == 0
    assert row == (2, 16)
