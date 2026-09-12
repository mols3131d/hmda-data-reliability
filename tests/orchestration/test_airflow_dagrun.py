"""실제 Airflow DAGRun의 상태와 영속 Asset evidence를 격리해서 검증한다.

Scheduler daemon은 실행하지 않으며 production task나 domain 함수를 대체하지 않는다.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
from collections.abc import Iterator
from contextlib import closing, suppress
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import duckdb
import pytest

from hmda_reliability.data_platform.artifacts import artifact_projection_id

pytestmark = [pytest.mark.integration, pytest.mark.timeout(240)]

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DAG_ID = "hmda_data_plane"
_RAW_TASK = "load_raw_hmda_loans"
_GATE_TASK = "evaluate_quality_gate"
_ANALYTICS_TASK = "build_dbt_loan_analytics"
_SOURCE_YEAR = 2025
_FIXTURE_ROW_COUNT = 1_000
_ACCEPTED_INCOME_NULL_COUNT = 161
_BLOCKING_INCOME_NULL_COUNT = 400


@dataclass
class _Runtime:
    root: Path
    env: dict[str, str]

    @property
    def database(self) -> Path:
        return self.root / "sandbox.duckdb"

    @property
    def source(self) -> Path:
        return self.root / "source"

    @property
    def metadata(self) -> Path:
        return self.root / "airflow" / "airflow.db"

    def airflow(self, label: str, *args: str) -> int:
        log_path = self.root / f"{label}.log"
        with (
            log_path.open("w", encoding="utf-8") as output,
            subprocess.Popen(
                [sys.executable, "-m", "airflow", *args],
                cwd=self.root,
                env=self.env,
                stdout=output,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            ) as process,
        ):
            try:
                return process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                pytest.fail(f"Airflow {label} timed out:\n{self.log(label)}")
            finally:
                if process.poll() is None:
                    with suppress(ProcessLookupError, PermissionError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait()

    def log(self, label: str) -> str:
        return (self.root / f"{label}.log").read_text(encoding="utf-8")

    def rows(self, query: str) -> list[dict[str, Any]]:
        with closing(
            sqlite3.connect(f"{self.metadata.as_uri()}?mode=ro", uri=True)
        ) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute(query)]

    def run(self, *, build: bool = True) -> int:
        configuration = {
            "database_path": str(self.database),
            "source_root": str(self.source),
            "source_year": _SOURCE_YEAR,
            "run_dbt_build": build,
        }
        return self.airflow(
            "run", "dags", "test", _DAG_ID, "-c", json.dumps(configuration)
        )

    def assert_run(self, state: str, expected_tasks: dict[str, str]) -> str:
        runs = self.rows("SELECT run_id, state, triggered_by FROM dag_run")
        assert len(runs) == 1
        assert runs[0]["state"] == state
        assert runs[0]["triggered_by"] == "TEST"
        tasks = self.rows("SELECT task_id, state FROM task_instance")
        assert {task["task_id"]: task["state"] for task in tasks} == expected_tasks
        assert self.rows("SELECT key FROM xcom") == []
        return runs[0]["run_id"]

    def events(self, run_id: str) -> dict[str, dict[str, Any]]:
        rows = self.rows(
            "SELECT ae.source_dag_id, ae.source_run_id, ae.source_task_id, "
            "ae.extra, a.uri "
            "FROM asset_event ae "
            "JOIN asset a ON ae.asset_id = a.id"
        )
        for row in rows:
            assert row["source_dag_id"] == _DAG_ID
            assert row["source_run_id"] == run_id
            if row["source_task_id"] == _RAW_TASK:
                assert row["uri"] == "hmda/raw/hmda_loans"
            elif row["source_task_id"] == _ANALYTICS_TASK:
                assert row["uri"] == "hmda/analytics/loan_analytics"
            else:
                message = f"예상치 못한 태스크 에셋 이벤트: {row['source_task_id']}"
                pytest.fail(message)
        assert len(rows) == len({row["source_task_id"] for row in rows})
        return {row["source_task_id"]: json.loads(row["extra"]) for row in rows}


def _protected_files() -> dict[str, tuple[int, int, str] | None]:
    result: dict[str, tuple[int, int, str] | None] = {}
    for relative in (
        "data/hmda_reliability.duckdb",
        "dbt/target/manifest.json",
        "dbt/target/run_results.json",
    ):
        path = _REPOSITORY_ROOT / relative
        if not path.exists():
            result[relative] = None
            continue
        with path.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        stat = path.stat()
        result[relative] = (stat.st_size, stat.st_mtime_ns, digest)
    return result


@pytest.fixture(scope="module", autouse=True)
def protect_repository_files() -> Iterator[None]:
    before = _protected_files()
    yield
    assert _protected_files() == before, "Repository database/artifacts changed"


@pytest.fixture
def runtime() -> Iterator[_Runtime]:
    temporary_root = _REPOSITORY_ROOT / ".local"
    temporary_root.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="airflow-test-", dir=temporary_root) as temporary:
        root = Path(temporary)
        for directory in ("src", "dbt"):
            shutil.copytree(
                _REPOSITORY_ROOT / directory,
                root / directory,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.egg-info", "target", "logs"
                ),
            )
        for directory in ("source", "airflow", "tmp", "home"):
            (root / directory).mkdir()
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("AIRFLOW", "HMDA_", "DBT_", "PYTHON"))
        }
        env.update(
            AIRFLOW_HOME=str(root / "airflow"),
            AIRFLOW_CONFIG=str(root / "airflow" / "airflow.cfg"),
            AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=f"sqlite:///{root}/airflow/airflow.db",
            AIRFLOW__CORE__DAGS_FOLDER=str(
                root / "src/hmda_reliability/orchestration/dags"
            ),
            AIRFLOW__CORE__LOAD_EXAMPLES="false",
            AIRFLOW__CORE__DAG_RUN_CONF_OVERRIDES_PARAMS="true",
            AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS="false",
            HMDA_RELIABILITY_DUCKDB_PATH=str(root / "sandbox.duckdb"),
            DBT_SEND_ANONYMOUS_USAGE_STATS="false",
            PYTHONPATH=str(root / "src"),
            PYTHONDONTWRITEBYTECODE="1",
            PATH=str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"],
            HOME=str(root / "home"),
            TMPDIR=str(root / "tmp"),
            OPENBLAS_NUM_THREADS="1",
            OMP_NUM_THREADS="1",
        )
        imported = subprocess.run(
            [
                sys.executable,
                "-c",
                "import hmda_reliability; print(hmda_reliability.__file__)",
            ],
            cwd=root,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        assert Path(imported.stdout.strip()).is_relative_to(root / "src")
        instance = _Runtime(root, env)
        for label, args in (
            ("migrate", ("db", "migrate")),
            ("serialize", ("dags", "reserialize")),
        ):
            return_code = instance.airflow(label, *args)
            assert return_code == 0, instance.log(label)
        yield instance
    assert not root.exists()


def _write_source(
    runtime: _Runtime,
    *,
    null_count: int = _ACCEPTED_INCOME_NULL_COUNT,
    loan_purpose: str = "1",
) -> None:
    with (runtime.source / f"year_{_SOURCE_YEAR}.csv").open(
        "w", newline="", encoding="utf-8"
    ) as output:
        writer = csv.writer(output)
        writer.writerow(
            (
                "activity_year",
                "loan_purpose",
                "action_taken",
                "loan_amount",
                "income",
                "state_code",
                "county_code",
            )
        )
        for index in range(_FIXTURE_ROW_COUNT):
            writer.writerow(
                (
                    _SOURCE_YEAR,
                    loan_purpose,
                    1,
                    200000 + index,
                    "NA" if index < null_count else 80,
                    "CA",
                    "06001",
                )
            )


def test_disabled_analytics_is_skipped_without_asset_update(runtime: _Runtime) -> None:
    _write_source(runtime)

    return_code = runtime.run(build=False)

    assert return_code == 0, runtime.log("run")
    run_id = runtime.assert_run(
        "success",
        {_RAW_TASK: "success", _GATE_TASK: "success", _ANALYTICS_TASK: "skipped"},
    )
    events = runtime.events(run_id)
    assert set(events) == {_RAW_TASK}
    assert events[_RAW_TASK]["hmda_loans_row_count"] == _FIXTURE_ROW_COUNT
    assert not (runtime.root / "dbt/target").exists()


def test_raw_failure_blocks_gate_and_analytics_without_events(
    runtime: _Runtime,
) -> None:
    return_code = runtime.run()

    assert return_code == 1, runtime.log("run")
    run_id = runtime.assert_run(
        "failed",
        {
            _RAW_TASK: "failed",
            _GATE_TASK: "upstream_failed",
            _ANALYTICS_TASK: "upstream_failed",
        },
    )
    assert runtime.events(run_id) == {}
    assert not (runtime.root / "dbt/target").exists()


def test_quality_gate_blocks_analytics_with_incident_evidence(
    runtime: _Runtime,
) -> None:
    _write_source(runtime, null_count=_BLOCKING_INCOME_NULL_COUNT)

    return_code = runtime.run()

    assert return_code == 1, runtime.log("run")
    run_id = runtime.assert_run(
        "failed",
        {
            _RAW_TASK: "success",
            _GATE_TASK: "failed",
            _ANALYTICS_TASK: "upstream_failed",
        },
    )
    events = runtime.events(run_id)
    assert set(events) == {_RAW_TASK}
    assert events[_RAW_TASK]["hmda_loans_row_count"] == _FIXTURE_ROW_COUNT
    assert "null_spike(income)" in runtime.log("run")
    assert "AirflowException" in runtime.log("run")
    assert not (runtime.root / "dbt/target").exists()


def test_success_promotes_candidate_and_records_analytics_update(
    runtime: _Runtime,
) -> None:
    _write_source(runtime)

    return_code = runtime.run()

    assert return_code == 0, runtime.log("run")
    run_id = runtime.assert_run(
        "success",
        {_RAW_TASK: "success", _GATE_TASK: "success", _ANALYTICS_TASK: "success"},
    )
    tasks = {
        row["task_id"]: row
        for row in runtime.rows(
            "SELECT task_id, start_date, end_date FROM task_instance"
        )
    }
    raw_end = datetime.fromisoformat(tasks[_RAW_TASK]["end_date"])
    gate_start = datetime.fromisoformat(tasks[_GATE_TASK]["start_date"])
    gate_end = datetime.fromisoformat(tasks[_GATE_TASK]["end_date"])
    analytics_start = datetime.fromisoformat(tasks[_ANALYTICS_TASK]["start_date"])
    assert raw_end <= gate_start
    assert gate_end <= analytics_start
    events = runtime.events(run_id)
    assert set(events) == {_RAW_TASK, _ANALYTICS_TASK}
    raw_evidence = events[_RAW_TASK]
    assert raw_evidence["execution_stage"] == "raw_load"
    assert raw_evidence["data_update"] is True
    assert raw_evidence["database_path"] == str(runtime.database)
    assert raw_evidence["source_root"] == str(runtime.source)
    assert raw_evidence["source_file_count"] == 1
    assert raw_evidence["source_year"] == _SOURCE_YEAR
    assert raw_evidence["hmda_loans_row_count"] == _FIXTURE_ROW_COUNT
    analytics = events[_ANALYTICS_TASK]
    assert analytics["data_update"] is True
    assert analytics["execution_stage"] == "analytics_build"
    assert analytics["return_code"] == 0
    manifest = Path(analytics["manifest_path"])
    results = Path(analytics["run_results_path"])
    for path in (manifest, results):
        assert path.is_relative_to(runtime.root / "dbt/target/runs")
        assert (
            path.read_bytes() == (runtime.root / "dbt/target" / path.name).read_bytes()
        )
    assert artifact_projection_id(manifest, results) == analytics["projection_id"]
    build_results = json.loads(results.read_text(encoding="utf-8"))["results"]
    successful_models = {
        row["unique_id"] for row in build_results if row["status"] == "success"
    }
    assert {
        "model.hmda_reliability.stg_hmda_loans",
        "model.hmda_reliability.mart_hmda_loan_outcomes",
    } <= successful_models
    assert all(row["status"] in {"success", "pass"} for row in build_results)
    with duckdb.connect(str(runtime.database), read_only=True) as connection:
        assert connection.execute("SELECT count(*) FROM raw.hmda_loans").fetchone() == (
            _FIXTURE_ROW_COUNT,
        )
        assert connection.execute(
            "SELECT count(*), count(income) FROM staging.stg_hmda_loans"
        ).fetchone() == (
            _FIXTURE_ROW_COUNT,
            _FIXTURE_ROW_COUNT - _ACCEPTED_INCOME_NULL_COUNT,
        )
        assert connection.execute(
            "SELECT application_count, approval_count, denial_count "
            "FROM marts.mart_hmda_loan_outcomes"
        ).fetchall() == [(_FIXTURE_ROW_COUNT, _FIXTURE_ROW_COUNT, 0)]


def test_dbt_failure_preserves_current_without_analytics_update(
    runtime: _Runtime,
) -> None:
    _write_source(runtime, loan_purpose="NA")
    current = runtime.root / "dbt/target"
    current.mkdir()
    previous = {
        "manifest.json": b'{"sentinel":"manifest"}',
        "run_results.json": b'{"sentinel":"results"}',
    }
    for filename, content in previous.items():
        (current / filename).write_bytes(content)

    return_code = runtime.run()

    assert return_code == 1, runtime.log("run")
    run_id = runtime.assert_run(
        "failed",
        {_RAW_TASK: "success", _GATE_TASK: "success", _ANALYTICS_TASK: "failed"},
    )
    assert set(runtime.events(run_id)) == {_RAW_TASK}
    for filename, content in previous.items():
        assert (current / filename).read_bytes() == content
    candidates = list((current / "runs").rglob("run_results.json"))
    assert len(candidates) == 1
    failed_results = json.loads(candidates[0].read_text(encoding="utf-8"))["results"]
    assert any(
        "loan_purpose" in result["unique_id"] and result["status"] == "fail"
        for result in failed_results
    )
