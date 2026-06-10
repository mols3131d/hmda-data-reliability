"""MVP pipeline runner 테스트."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from project_pivot.pipeline import MvpPipelineRunRequest, run_mvp_pipeline
from project_pivot.taxi_data import DuckDBConnectionManager
from project_pivot.taxi_data.sql import quote_string_literal


def test_run_mvp_pipeline_without_dbt_build_creates_lifecycle_report(
    tmp_path: Path,
) -> None:
    """fixture artifact로 runner contract를 검증한다."""

    source_root = tmp_path / "raw"
    source_root.mkdir()
    zone_csv_path = _write_zone_csv(source_root)
    tripdata_path = _write_tripdata_parquet(source_root)
    manifest_path = _write_manifest(tmp_path)
    run_results_path = _write_run_results(tmp_path)
    report_path = tmp_path / "pipeline_report.md"

    result = run_mvp_pipeline(
        MvpPipelineRunRequest(
            database_path=tmp_path / "project_pivot.duckdb",
            source_root=source_root,
            zone_csv_path=zone_csv_path,
            dbt_manifest_path=manifest_path,
            dbt_run_results_path=run_results_path,
            report_path=report_path,
            run_dbt_build=False,
            partition_date=date(2024, 1, 15),
        )
    )

    assert tripdata_path.exists()
    assert result.status == "completed"
    assert result.raw_load.yellow_tripdata_row_count == 4
    assert result.dbt_build is None
    assert result.lifecycle.detected_incident_types == ["volume_drop"]
    assert result.lifecycle.affected_assets == [
        "stg_yellow_tripdata",
        "mart_daily_taxi_trips",
    ]
    assert result.lifecycle.detection_success_rate == 1.0
    assert report_path.exists()


def _write_zone_csv(source_root: Path) -> Path:
    path = source_root / "taxi_zone_lookup.csv"
    path.write_text(
        "\n".join(
            [
                "LocationID,Borough,Zone,service_zone",
                "1,EWR,Newark Airport,EWR",
                "2,Queens,Jamaica Bay,Boro Zone",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _write_tripdata_parquet(source_root: Path) -> Path:
    path = source_root / "yellow_tripdata_2024-01.parquet"
    target_path = quote_string_literal(str(path))
    with DuckDBConnectionManager() as connection:
        connection.execute(
            f"""
            COPY (
                SELECT
                    vendor_id AS VendorID,
                    TIMESTAMP '2024-01-15 08:00:00'
                        + vendor_id * INTERVAL '1 minute'
                        AS tpep_pickup_datetime,
                    TIMESTAMP '2024-01-15 08:15:00'
                        + vendor_id * INTERVAL '1 minute'
                        AS tpep_dropoff_datetime,
                    1::BIGINT AS passenger_count,
                    3.5 + vendor_id AS trip_distance,
                    1 AS PULocationID,
                    2 AS DOLocationID,
                    1::BIGINT AS payment_type,
                    10.0 AS fare_amount,
                    12.5 + vendor_id AS total_amount
                FROM range(4) AS rows(vendor_id)
            )
            TO {target_path}
            (FORMAT PARQUET)
            """
        )
    return path


def _write_manifest(tmp_path: Path) -> Path:
    manifest_path = tmp_path / "manifest.json"
    manifest = {
        "sources": {
            "source.project_pivot.raw.yellow_tripdata": {
                "name": "yellow_tripdata",
                "schema": "raw",
                "resource_type": "source",
                "depends_on": {"nodes": []},
            }
        },
        "nodes": {
            "model.project_pivot.stg_yellow_tripdata": {
                "name": "stg_yellow_tripdata",
                "resource_type": "model",
                "depends_on": {
                    "nodes": ["source.project_pivot.raw.yellow_tripdata"]
                },
            },
            "model.project_pivot.mart_daily_taxi_trips": {
                "name": "mart_daily_taxi_trips",
                "resource_type": "model",
                "depends_on": {
                    "nodes": ["model.project_pivot.stg_yellow_tripdata"]
                },
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _write_run_results(tmp_path: Path) -> Path:
    run_results_path = tmp_path / "run_results.json"
    run_results_path.write_text("{}", encoding="utf-8")
    return run_results_path
