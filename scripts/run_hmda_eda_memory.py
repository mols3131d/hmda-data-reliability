#!/usr/bin/env python3
"""HMDA EDA representative fixture를 process memory budget 안에서 3회 실행한다."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any

from project_pivot.hmda_data.eda_fixture import validate_hmda_eda_fixture
from project_pivot.hmda_data.eda_memory import (
    assess_memory_runs,
    parse_gnu_time_report,
)

ROOT = Path(__file__).resolve().parents[1]
PROCESS_LIMIT_BYTES = 3 * 1024**3
DUCKDB_LIMIT = "1600MB"
DUCKDB_THREADS = 2
TIMEOUT = "15m"
TEMP_DISK_LIMIT_BYTES = 10 * 1024**3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture-directory",
        type=Path,
        default=Path("data/samples/hmda/eda-memory-v1"),
    )
    parser.add_argument(
        "--report-path",
        type=Path,
        default=Path("notes/artifacts/hmda_eda_memory_report.json"),
    )
    return parser.parse_args()


def _command_path(command: str) -> str:
    path = shutil.which(command)
    if path is None:
        raise RuntimeError(f"Required command is not available: {command}")
    return path


def _run_systemd(
    command: list[str],
    unit_name: str,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            _command_path("systemd-run"),
            "--user",
            "--wait",
            "--pipe",
            "--collect",
            f"--unit={unit_name}",
            "-p",
            f"WorkingDirectory={ROOT}",
            "-p",
            f"MemoryMax={PROCESS_LIMIT_BYTES}",
            "-p",
            "MemorySwapMax=0",
            *command,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _verify_hard_limit() -> dict[str, Any]:
    control_unit = f"hmda-eda-memory-control-{uuid.uuid4().hex[:8]}"
    control = _run_systemd([_command_path("true")], control_unit)
    if control.returncode != 0:
        raise RuntimeError(
            "systemd user memory control is unavailable:\n"
            f"{control.stdout}\n{control.stderr}"
        )

    probe_unit = f"hmda-eda-memory-probe-{uuid.uuid4().hex[:8]}"
    probe = subprocess.run(
        [
            _command_path("systemd-run"),
            "--user",
            "--wait",
            "--pipe",
            "--collect",
            f"--unit={probe_unit}",
            "-p",
            f"WorkingDirectory={ROOT}",
            "-p",
            "MemoryMax=134217728",
            "-p",
            "MemorySwapMax=0",
            sys.executable,
            "-c",
            "bytearray(256 * 1024 * 1024)",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    probe_evidence = (probe.stdout + probe.stderr).strip()
    if probe.returncode == 0 or "oom-kill" not in probe_evidence.lower():
        raise RuntimeError(
            f"systemd probe did not produce OOM enforcement evidence:\n{probe_evidence}"
        )
    return {
        "control_exit_code": control.returncode,
        "probe_exit_code": probe.returncode,
        "probe_evidence": probe_evidence,
    }


def _directory_size(path: Path) -> int:
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())


def _run_once(fixture_directory: Path, run_number: int) -> dict[str, Any]:
    run_directory = Path(tempfile.mkdtemp(prefix=f"hmda-eda-memory-{run_number}-"))
    duckdb_temp = run_directory / "duckdb-temp"
    output_path = run_directory / "result.json"
    time_path = run_directory / "time.txt"
    environment = {
        "HMDA_EDA_FIXTURE_DIR": str(fixture_directory),
        "HMDA_EDA_TEMP_DIR": str(duckdb_temp),
        "HMDA_EDA_RESULT_PATH": str(output_path),
        "HMDA_EDA_DUCKDB_LIMIT": DUCKDB_LIMIT,
        "HMDA_EDA_DUCKDB_THREADS": str(DUCKDB_THREADS),
    }
    env_arguments = [f"{key}={value}" for key, value in environment.items()]
    command = [
        _command_path("time"),
        "-v",
        "-o",
        str(time_path),
        _command_path("timeout"),
        "--signal=TERM",
        TIMEOUT,
        _command_path("env"),
        *env_arguments,
        _command_path("uv"),
        "run",
        "pytest",
        "-n",
        "0",
        "-m",
        "memory",
        "tests/hmda_data/test_eda_memory.py",
        "-q",
    ]
    unit_name = f"hmda-eda-memory-{run_number}-{uuid.uuid4().hex[:8]}"
    completed = _run_systemd(command, unit_name)
    timing = (
        parse_gnu_time_report(time_path.read_text(encoding="utf-8"))
        if time_path.is_file()
        else {"peak_rss_kib": 0, "elapsed_seconds": 0.0}
    )
    output_validation = "failed"
    worker_result: dict[str, Any] = {}
    if output_path.is_file():
        worker_result = json.loads(output_path.read_text(encoding="utf-8"))
        output_validation = worker_result.get("output_validation", "failed")
    resource_text = (completed.stdout + completed.stderr).lower()
    resource_status = (
        "failed"
        if completed.returncode != 0
        or "timeout" in resource_text
        or "oom" in resource_text
        or "killed" in resource_text
        else "passed"
    )
    result = {
        "run": run_number,
        "unit": unit_name,
        "exit_code": completed.returncode,
        "resource_status": resource_status,
        "output_validation": output_validation,
        "peak_rss_kib": timing["peak_rss_kib"],
        "elapsed_seconds": timing["elapsed_seconds"],
        "temp_disk_bytes": _directory_size(run_directory),
        "systemd_evidence": (completed.stdout + completed.stderr).strip(),
        "environment": worker_result.get("environment"),
    }
    shutil.rmtree(run_directory)
    return result


def main() -> int:
    args = parse_args()
    fixture_directory = args.fixture_directory.expanduser().resolve()
    _, manifest = validate_hmda_eda_fixture(fixture_directory)
    preflight = _verify_hard_limit()
    runs = [_run_once(fixture_directory, run_number) for run_number in range(1, 4)]
    assessment = assess_memory_runs(
        runs,
        process_limit_bytes=PROCESS_LIMIT_BYTES,
        temp_disk_limit_bytes=TEMP_DISK_LIMIT_BYTES,
    )
    report = {
        "fixture_version": manifest.version,
        "process_limit_bytes": PROCESS_LIMIT_BYTES,
        "swap_limit_bytes": 0,
        "duckdb_limit": DUCKDB_LIMIT,
        "duckdb_threads": DUCKDB_THREADS,
        "timeout": TIMEOUT,
        "temp_disk_limit_bytes": TEMP_DISK_LIMIT_BYTES,
        "preflight": preflight,
        "runs": runs,
        "assessment": assessment,
    }
    report_path = args.report_path.expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if assessment["status"] in {"passed", "improvement_needed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
