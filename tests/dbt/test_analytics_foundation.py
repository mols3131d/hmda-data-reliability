"""실제 dbt build로 staging 타입·mart metric·lineage·재실행과 quality 실패를 검증한다.

운영 runner의 quality gate와 artifact promotion은 Data Operations가 검증한다.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import cast

import pytest

from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.hmda_data import load_hmda_loans

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"


@pytest.mark.component
def test_dbt_profile_requires_caller_database_path() -> None:
    """dbt profile은 application과 별도의 DuckDB path fallback을 소유하지 않는다."""

    profile = (DBT_PROJECT_DIR / "profiles.yml").read_text(encoding="utf-8")

    assert "path: \"{{ env_var('HMDA_RELIABILITY_DUCKDB_PATH') }}\"" in profile


@pytest.mark.integration
def test_dbt_build_creates_artifacts_lineage_and_idempotent_mart(
    tmp_path: Path,
) -> None:
    """임시 DuckDB raw fixture로 dbt build 계약을 검증한다."""

    database_path = tmp_path / "hmda_reliability.duckdb"
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

    manifest_path = tmp_path / "dbt-target" / "manifest.json"
    run_results_path = tmp_path / "dbt-target" / "run_results.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert run_results_path.exists()
    assert _node_id(manifest, "model", "stg_hmda_loans") is not None
    assert _node_id(manifest, "model", "mart_hmda_loan_outcomes") is not None
    assert "source.hmda_reliability.raw.hmda_loans" in manifest["sources"]
    assert _depends_on(
        manifest,
        model_name="stg_hmda_loans",
        dependency="source.hmda_reliability.raw.hmda_loans",
    )
    assert _depends_on(
        manifest,
        model_name="mart_hmda_loan_outcomes",
        dependency=_node_id(manifest, "model", "stg_hmda_loans"),
    )
    assert first_stats == second_stats == (5, 5)
    assert (
        first_metric_rows
        == second_metric_rows
        == [
            (2024, "CA", 1, 1, 1, 0, 1.0, 200000.0, 80.0),
            (2025, "CA", 1, 2, 1, 0, 0.5, 400000.0, 125.0),
            (2025, "CA", 31, 1, 0, 1, 0.0, 300000.0, 90.0),
            (2025, "NY", 31, 2, 0, 2, 0.0, 400000.0, 95.0),
            (2025, "TX", 1, 3, 2, 0, 0.666667, 150000.0, 75.0),
        ]
    )


@pytest.mark.integration
def test_dbt_quality_tests_detect_source_staging_and_mart_violations(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "hmda_reliability.duckdb"
    with DuckDBConnectionManager(database_path) as connection:
        load_hmda_loans(connection, [_write_hmda_csv(tmp_path)])

    _run_dbt(database_path, "build")
    with DuckDBConnectionManager(database_path) as connection:
        connection.execute(
            "UPDATE raw.hmda_loans SET source_year = NULL WHERE state_code = 'TX'"
        )
        connection.execute(
            "INSERT INTO marts.mart_hmda_loan_outcomes "
            "SELECT * FROM marts.mart_hmda_loan_outcomes WHERE state_code = 'NY'"
        )
        connection.execute(
            "UPDATE marts.mart_hmda_loan_outcomes SET mart_grain_key = NULL "
            "WHERE state_code = 'TX'"
        )

    _run_dbt(database_path, "test", expected_returncode=1)

    target = tmp_path / "dbt-target"
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    run_results = json.loads((target / "run_results.json").read_text(encoding="utf-8"))
    unexpected_results = {
        result["unique_id"]: result["status"]
        for result in run_results["results"]
        if result["status"] not in {"pass", "fail"}
    }
    assert not unexpected_results, f"Unexpected dbt test statuses: {unexpected_results}"
    failed_nodes = [
        manifest["nodes"][result["unique_id"]]
        for result in run_results["results"]
        if result["status"] == "fail"
    ]
    assert {
        (
            node["test_metadata"]["name"],
            node["column_name"],
            tuple(node["depends_on"]["nodes"]),
        )
        for node in failed_nodes
    } == {
        ("not_null", "source_year", ("source.hmda_reliability.raw.hmda_loans",)),
        ("not_null", "source_year", ("model.hmda_reliability.stg_hmda_loans",)),
        (
            "not_null",
            "mart_grain_key",
            ("model.hmda_reliability.mart_hmda_loan_outcomes",),
        ),
        (
            "unique",
            "mart_grain_key",
            ("model.hmda_reliability.mart_hmda_loan_outcomes",),
        ),
    }


def _run_dbt(
    database_path: Path, command: str, *, expected_returncode: int = 0
) -> None:
    env = os.environ.copy()
    env["DBT_PROFILES_DIR"] = str(DBT_PROJECT_DIR)
    env["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    env["HMDA_RELIABILITY_DUCKDB_PATH"] = str(database_path)
    arguments = [
        "dbt",
        command,
        "--project-dir",
        str(DBT_PROJECT_DIR),
        "--log-path",
        str(database_path.parent / "dbt-logs"),
    ]
    if command in {"build", "test"}:
        arguments.extend(["--target-path", str(database_path.parent / "dbt-target")])
    result = subprocess.run(
        arguments,
        check=False,
        capture_output=True,
        env=env,
        text=True,
    )
    assert result.returncode == expected_returncode, result.stdout + result.stderr


def _write_hmda_csv(tmp_path: Path) -> Path:
    path = tmp_path / "year_2025.csv"
    path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,1,4,450000,130,CA,06001",
                "2025,31,3,420000,95,NY,36061",
                "2025,31,7,380000,95,NY,36061",
                "2025,1,1,invalid,Exempt,,",
                "2024,1,1,200000,80,CA,06001",
                "2025,31,3,300000,90,CA,06001",
                "2025,1,1,100000,50,TX,48001",
                "2025,1,2,200000,100,TX,48001",
                "2025,1,4,invalid,Exempt,TX,",
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
        assert count is not None and count[0] == 10

        column_types = dict(
            connection.execute(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'staging' AND table_name = 'stg_hmda_loans'"
            ).fetchall()
        )
        for column, expected_type in {
            "activity_year": "INTEGER",
            "loan_purpose": "INTEGER",
            "action_taken": "INTEGER",
            "source_year": "INTEGER",
            "state_code": "VARCHAR",
            "county_code": "VARCHAR",
            "source_file": "VARCHAR",
            "loan_amount": "DOUBLE",
            "income": "DOUBLE",
        }.items():
            assert column_types[column] == expected_type

        null_row = connection.execute(
            "SELECT state_code, county_code, loan_amount, income "
            "FROM staging.stg_hmda_loans WHERE state_code IS NULL"
        ).fetchone()
        assert null_row is not None
        assert null_row[0] is None
        assert null_row[1] is None
        assert null_row[2] is None
        assert null_row[3] is None

        eligible_null_row = connection.execute(
            "SELECT county_code, loan_amount, income "
            "FROM staging.stg_hmda_loans "
            "WHERE state_code = 'TX' AND action_taken = 4"
        ).fetchall()
        assert eligible_null_row == [(None, None, None)]


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
    return cast(list[tuple[int, str, int, int, int, int, float, float, float]], rows)


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
