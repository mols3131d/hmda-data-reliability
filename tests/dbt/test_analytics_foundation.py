"""dbt 분석 파운데이션 통합 테스트."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import cast

import pytest

from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import load_hmda_loans

pytestmark = pytest.mark.integration

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"


def test_dbt_build_creates_artifacts_lineage_and_idempotent_mart(
    tmp_path: Path,
) -> None:
    """임시 DuckDB raw fixture로 dbt build 계약을 검증한다."""

    database_path = tmp_path / "project_pivot.duckdb"
    hmda_csv_path = _write_hmda_csv(tmp_path)

    with DuckDBConnectionManager(database_path) as connection:
        load_hmda_loans(connection, [hmda_csv_path])

    _run_dbt(database_path, "debug")
    _run_dbt(database_path, "build")
    _assert_staging_oracle(database_path)
    first_stats = _mart_stats(database_path)
    first_metric_rows = _mart_metric_rows(database_path)

    _run_dbt(database_path, "build")
    _assert_staging_oracle(database_path)
    second_stats = _mart_stats(database_path)
    second_metric_rows = _mart_metric_rows(database_path)

    manifest_path = DBT_PROJECT_DIR / "target" / "manifest.json"
    run_results_path = DBT_PROJECT_DIR / "target" / "run_results.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert run_results_path.exists()
    assert _node_id(manifest, "model", "stg_hmda_loans") is not None
    assert _node_id(manifest, "model", "mart_hmda_loan_outcomes") is not None
    assert "source.project_pivot.raw.hmda_loans" in manifest["sources"]
    assert _depends_on(
        manifest,
        model_name="stg_hmda_loans",
        dependency="source.project_pivot.raw.hmda_loans",
    )
    assert _depends_on(
        manifest,
        model_name="mart_hmda_loan_outcomes",
        dependency=_node_id(manifest, "model", "stg_hmda_loans"),
    )
    assert first_stats == second_stats == (2, 2)
    assert (
        first_metric_rows
        == second_metric_rows
        == [
            (2025, "CA", 1, 2, 2, 0, 1.0, 400000.0, 125.0),
            (2025, "NY", 31, 2, 0, 2, 0.0, 400000.0, 95.0),
        ]
    )


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


def _write_hmda_csv(tmp_path: Path) -> Path:
    path = tmp_path / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,1,2,450000,130,CA,06001",
                "2025,31,3,420000,95,NY,36061",
                "2025,31,7,380000,95,NY,36061",
                "2025,1,1,invalid,Exempt,,",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _assert_staging_oracle(database_path: Path) -> None:
    with DuckDBConnectionManager(database_path, read_only=True) as connection:
        count = connection.execute(
            "SELECT count(*) FROM staging.stg_hmda_loans"
        ).fetchone()
        assert count is not None and count[0] == 5

        column_types = dict(
            connection.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'staging' AND table_name = 'stg_hmda_loans'"
            ).fetchall()
        )
        assert column_types["loan_amount"] == "DOUBLE"
        assert column_types["income"] == "DOUBLE"

        null_row = connection.execute(
            "SELECT state_code, county_code, loan_amount, income "
            "FROM staging.stg_hmda_loans WHERE state_code IS NULL"
        ).fetchone()
        assert null_row is not None
        assert null_row[0] is None
        assert null_row[1] is None
        assert null_row[2] is None
        assert null_row[3] is None


def _mart_stats(database_path: Path) -> tuple[int, int]:
    with DuckDBConnectionManager(database_path, read_only=True) as connection:
        result = connection.execute(
            """
            SELECT
                count(*) AS row_count,
                count(DISTINCT mart_grain_key) AS grain_count
            FROM marts.mart_hmda_loan_outcomes
            """
        ).fetchone()
    assert result is not None
    return int(result[0]), int(result[1])


def _mart_metric_rows(
    database_path: Path,
) -> list[tuple[int, str, int, int, int, int, float, float, float]]:
    with DuckDBConnectionManager(database_path, read_only=True) as connection:
        rows = connection.execute(
            """
            SELECT
                activity_year,
                state_code,
                loan_purpose,
                application_count,
                approval_count,
                denial_count,
                approval_rate,
                average_loan_amount,
                average_income
            FROM marts.mart_hmda_loan_outcomes
            ORDER BY activity_year, state_code, loan_purpose
            """
        ).fetchall()
    return [
        (
            int(row[0]),
            str(row[1]),
            int(row[2]),
            int(row[3]),
            int(row[4]),
            int(row[5]),
            float(row[6]),
            float(row[7]),
            float(row[8]),
        )
        for row in rows
    ]


def _node_id(manifest: dict[str, object], resource_type: str, name: str) -> str | None:
    nodes = _object_dict(manifest["nodes"])
    for node_id, node in nodes.items():
        node_data = _object_dict(node)
        if node_data["resource_type"] == resource_type and node_data["name"] == name:
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
    manifest_nodes = _object_dict(manifest["nodes"])
    node = _object_dict(manifest_nodes[node_id])
    depends_on = _object_dict(node["depends_on"])
    nodes = depends_on["nodes"]
    assert isinstance(nodes, list)
    return dependency in nodes


def _object_dict(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return cast(dict[str, object], value)
