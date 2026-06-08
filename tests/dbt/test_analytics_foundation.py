"""dbt 분석 파운데이션 통합 테스트."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from project_pivot.taxi_data import (
    DuckDBConnectionManager,
    load_taxi_zones,
    load_yellow_tripdata,
)
from project_pivot.taxi_data.sql import quote_string_literal

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"


def test_dbt_build_creates_artifacts_lineage_and_idempotent_mart(
    tmp_path: Path,
) -> None:
    """임시 DuckDB raw fixture로 dbt build 계약을 검증한다."""

    database_path = tmp_path / "project_pivot.duckdb"
    zone_csv_path = _write_zone_csv(tmp_path)
    tripdata_path = _write_tripdata_parquet(tmp_path)

    with DuckDBConnectionManager(database_path) as connection:
        load_taxi_zones(connection, zone_csv_path)
        load_yellow_tripdata(connection, [tripdata_path])

    _run_dbt(database_path, "debug")
    _run_dbt(database_path, "build")
    first_stats = _mart_stats(database_path)

    _run_dbt(database_path, "build")
    second_stats = _mart_stats(database_path)

    manifest_path = DBT_PROJECT_DIR / "target" / "manifest.json"
    run_results_path = DBT_PROJECT_DIR / "target" / "run_results.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert run_results_path.exists()
    assert _node_id(manifest, "model", "stg_yellow_tripdata") is not None
    assert _node_id(manifest, "model", "stg_taxi_zones") is not None
    assert _node_id(manifest, "model", "mart_daily_taxi_trips") is not None
    assert "source.project_pivot.raw.yellow_tripdata" in manifest["sources"]
    assert "source.project_pivot.raw.taxi_zones" in manifest["sources"]
    assert _depends_on(
        manifest,
        model_name="stg_yellow_tripdata",
        dependency="source.project_pivot.raw.yellow_tripdata",
    )
    assert _depends_on(
        manifest,
        model_name="mart_daily_taxi_trips",
        dependency=_node_id(manifest, "model", "stg_yellow_tripdata"),
    )
    assert first_stats == second_stats == (4, 4)


def _run_dbt(database_path: Path, command: str) -> None:
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(DBT_PROJECT_DIR)
    env["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    env["PROJECT_PIVOT_DUCKDB_PATH"] = str(database_path)
    result = subprocess.run(
        ["dbt", command, "--project-dir", str(DBT_PROJECT_DIR)],
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def _write_zone_csv(tmp_path: Path) -> Path:
    path = tmp_path / "taxi_zone_lookup.csv"
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


def _write_tripdata_parquet(tmp_path: Path) -> Path:
    path = tmp_path / "yellow_tripdata_2024-01.parquet"
    target_path = quote_string_literal(str(path))
    with DuckDBConnectionManager() as connection:
        connection.execute(
            f"""
            COPY (
                SELECT
                    1 AS VendorID,
                    TIMESTAMP '2024-01-01 08:00:00'
                        + day_offset * INTERVAL '1 day'
                        + row_number * INTERVAL '1 minute'
                        AS tpep_pickup_datetime,
                    TIMESTAMP '2024-01-01 08:15:00'
                        + day_offset * INTERVAL '1 day'
                        + row_number * INTERVAL '1 minute'
                        AS tpep_dropoff_datetime,
                    1::BIGINT AS passenger_count,
                    3.5 + row_number AS trip_distance,
                    1 AS PULocationID,
                    2 AS DOLocationID,
                    1::BIGINT AS payment_type,
                    10.0 AS fare_amount,
                    12.5 + row_number AS total_amount
                FROM range(4) AS days(day_offset)
                CROSS JOIN range(4) AS rows(row_number)
            )
            TO {target_path}
            (FORMAT PARQUET)
            """
        )
    return path


def _mart_stats(database_path: Path) -> tuple[int, int]:
    with DuckDBConnectionManager(database_path, read_only=True) as connection:
        result = connection.execute(
            """
            SELECT
                count(*) AS row_count,
                count(DISTINCT mart_grain_key) AS grain_count
            FROM marts.mart_daily_taxi_trips
            """
        ).fetchone()
    assert result is not None
    return int(result[0]), int(result[1])


def _node_id(manifest: dict[str, object], resource_type: str, name: str) -> str | None:
    nodes = manifest["nodes"]
    assert isinstance(nodes, dict)
    for node_id, node in nodes.items():
        assert isinstance(node, dict)
        if node["resource_type"] == resource_type and node["name"] == name:
            return str(node_id)
    return None


def _depends_on(
    manifest: dict[str, object],
    *,
    model_name: str,
    dependency: str | None,
) -> bool:
    if dependency is None:
        return False
    node_id = _node_id(manifest, "model", model_name)
    if node_id is None:
        return False
    node = manifest["nodes"][node_id]
    assert isinstance(node, dict)
    depends_on = node["depends_on"]
    assert isinstance(depends_on, dict)
    nodes = depends_on["nodes"]
    assert isinstance(nodes, list)
    return dependency in nodes
