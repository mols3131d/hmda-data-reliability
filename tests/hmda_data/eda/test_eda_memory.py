"""HMDA EDA process-level memory workload 테스트."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import pytest

from project_pivot.hmda_data.eda import (
    prepare_hmda_eda_fixture,
    run_hmda_eda_memory_workload,
)
from scripts import run_hmda_eda_memory as runner

VALID_TIME_REPORT = """
Elapsed (wall clock) time (h:mm:ss or m:ss): 0:01.50
Maximum resident set size (kbytes): 123456
"""
VALID_WORKER_RESULT = {
    "output_validation": "passed",
    "environment": {"python": "3.13", "duckdb": "1.3"},
}


@pytest.mark.memory
def test_hmda_eda_representative_memory_workload() -> None:
    """Runner가 제공한 대표 fixture의 결과 invariant를 검증한다."""

    fixture_directory = Path(os.environ["HMDA_EDA_FIXTURE_DIR"])
    temp_directory = Path(os.environ["HMDA_EDA_TEMP_DIR"])
    output_path = Path(os.environ["HMDA_EDA_RESULT_PATH"])
    result = run_hmda_eda_memory_workload(
        fixture_directory,
        temp_directory=temp_directory,
        output_path=output_path,
        memory_limit=os.environ["HMDA_EDA_DUCKDB_LIMIT"],
        threads=int(os.environ["HMDA_EDA_DUCKDB_THREADS"]),
    )

    assert result["status"] == "passed"
    assert result["output_validation"] == "passed"


def _run_with_auxiliary_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    time_report: str | None = VALID_TIME_REPORT,
    worker_output: str | None = json.dumps(VALID_WORKER_RESULT),
    return_code: int = 0,
) -> tuple[dict[str, Any], Path, list[str]]:
    run_directory = tmp_path / "run"
    executed_command: list[str] = []

    def make_run_directory(*_args: object, **_kwargs: object) -> str:
        run_directory.mkdir()
        return str(run_directory)

    def fake_systemd(
        command: list[str],
        _unit_name: str,
    ) -> subprocess.CompletedProcess[str]:
        executed_command.extend(command)
        time_path = Path(command[command.index("-o") + 1])
        output_argument = next(
            item for item in command if item.startswith("HMDA_EDA_RESULT_PATH=")
        )
        output_path = Path(output_argument.partition("=")[2])
        if time_report is not None:
            time_path.write_text(time_report, encoding="utf-8")
        if worker_output is not None:
            output_path.write_text(worker_output, encoding="utf-8")
        return subprocess.CompletedProcess(command, return_code, "", "")

    monkeypatch.setattr(tempfile, "mkdtemp", make_run_directory)
    monkeypatch.setattr(runner, "_command_path", lambda command: command)
    monkeypatch.setattr(runner, "_run_systemd", fake_systemd)
    result = runner._run_once(tmp_path / "fixture", 1)
    return result, run_directory, executed_command


@pytest.mark.unit
def test_memory_runner_malformed_time_report_is_failed_and_cleaned(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result, run_directory, command = _run_with_auxiliary_output(
        monkeypatch,
        tmp_path,
        time_report="not a GNU time report",
    )

    assert result["output_validation"] == "failed"
    assert "GNU time report is invalid" in result["failure_reason"]
    assert "LC_ALL=C" in command
    assert not run_directory.exists()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("worker_output", "expected_reason"),
    [
        ("not-json", "worker result JSON is invalid"),
        (None, "worker result JSON is missing"),
    ],
)
def test_memory_runner_invalid_worker_output_is_failed_and_cleaned(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    worker_output: str | None,
    expected_reason: str,
) -> None:
    result, run_directory, _ = _run_with_auxiliary_output(
        monkeypatch,
        tmp_path,
        worker_output=worker_output,
    )

    assert result["output_validation"] == "failed"
    assert expected_reason in result["failure_reason"]
    assert not run_directory.exists()


@pytest.mark.unit
def test_memory_runner_success_cleans_run_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    result, run_directory, _ = _run_with_auxiliary_output(monkeypatch, tmp_path)

    assert result["failure_reason"] is None
    assert result["resource_status"] == "passed"
    assert result["output_validation"] == "passed"
    assert not run_directory.exists()


@pytest.mark.component
def test_memory_report_includes_fixture_provenance_and_failure(
    tmp_path: Path,
) -> None:
    manifest = prepare_hmda_eda_fixture(tmp_path, row_count=100, seed=7)
    failed_run = {
        "run": 1,
        "exit_code": 0,
        "resource_status": "passed",
        "output_validation": "failed",
        "peak_rss_kib": 0,
        "elapsed_seconds": 0.0,
        "temp_disk_bytes": 0,
        "failure_reason": "worker result JSON is malformed",
    }
    report = runner._build_report(
        tmp_path,
        manifest,
        {"control_exit_code": 0},
        [failed_run, {**failed_run, "run": 2}, {**failed_run, "run": 3}],
    )

    assert report["fixture"]["fixture_version"] == manifest.version
    assert report["fixture"]["fixture_directory"] == str(tmp_path.resolve())
    assert report["fixture"]["manifest_sha256"].startswith("sha256:")
    assert report["fixture"]["schema_fingerprint"].startswith("sha256:")
    assert report["fixture"]["files"] == [
        {
            "path": manifest.files[0].path,
            "size_bytes": manifest.files[0].size_bytes,
            "sha256": manifest.files[0].sha256,
        }
    ]
    assert report["runs"][0]["failure_reason"] == ("worker result JSON is malformed")
    assert report["assessment"]["status"] == "failed"


@pytest.mark.component
def test_memory_runner_preflight_failure_writes_final_report(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    fixture_directory = tmp_path / "fixture"
    report_path = tmp_path / "report.json"
    prepare_hmda_eda_fixture(fixture_directory, row_count=100, seed=7)
    monkeypatch.setattr(
        runner,
        "parse_args",
        lambda: argparse.Namespace(
            fixture_directory=fixture_directory,
            report_path=report_path,
        ),
    )
    monkeypatch.setattr(
        runner,
        "_verify_hard_limit",
        lambda: (_ for _ in ()).throw(RuntimeError("systemd unavailable")),
    )

    exit_code = runner.main()
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert report["fixture"]["manifest_sha256"].startswith("sha256:")
    assert report["preflight"] == {
        "status": "failed",
        "failure_reason": "systemd unavailable",
    }
    assert report["runs"] == []
    assert report["assessment"] == {
        "status": "failed",
        "reason": "memory runner preflight failed: systemd unavailable",
    }
