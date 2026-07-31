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

from project_pivot.hmda_data.eda_fixture import (
    HMDAEDAFixtureManifest,
    hmda_eda_fixture_provenance,
    validate_hmda_eda_fixture,
)
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
    unit_name = f"hmda-eda-memory-{run_number}-{uuid.uuid4().hex[:8]}"
    result = {
        "run": run_number,
        "unit": unit_name,
        "exit_code": None,
        "resource_status": "failed",
        "output_validation": "failed",
        "peak_rss_kib": 0,
        "elapsed_seconds": 0.0,
        "temp_disk_bytes": 0,
        "systemd_evidence": "",
        "environment": None,
        "failure_reason": None,
    }
    failures: list[str] = []
    try:
        command = [
            _command_path("env"),
            "LC_ALL=C",
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
        completed = _run_systemd(command, unit_name)
        result["exit_code"] = completed.returncode
        systemd_evidence = (completed.stdout + completed.stderr).strip()
        result["systemd_evidence"] = systemd_evidence
        resource_text = systemd_evidence.lower()
        result["resource_status"] = (
            "failed"
            if completed.returncode != 0
            or "timeout" in resource_text
            or "oom" in resource_text
            or "killed" in resource_text
            else "passed"
        )
        if result["resource_status"] == "failed":
            failures.append("process or resource control reported failure")

        if not time_path.is_file():
            failures.append("GNU time report is missing")
        else:
            try:
                timing = parse_gnu_time_report(time_path.read_text(encoding="utf-8"))
                result.update(timing)
            except (OSError, UnicodeError, ValueError) as error:
                failures.append(f"GNU time report is invalid: {error}")

        worker_result: dict[str, Any] = {}
        if not output_path.is_file():
            failures.append("worker result JSON is missing")
        else:
            try:
                loaded_result = json.loads(output_path.read_text(encoding="utf-8"))
                if not isinstance(loaded_result, dict):
                    raise ValueError("worker result must be a JSON object")
                worker_result = loaded_result
            except (json.JSONDecodeError, OSError, UnicodeError, ValueError) as error:
                failures.append(f"worker result JSON is invalid: {error}")
        result["environment"] = worker_result.get("environment")
        if worker_result.get("output_validation") == "passed":
            result["output_validation"] = "passed"
        else:
            failures.append("worker output validation did not pass")
    except (OSError, RuntimeError) as error:
        failures.append(f"memory run could not execute: {error}")
    finally:
        try:
            result["temp_disk_bytes"] = _directory_size(run_directory)
        except OSError as error:
            failures.append(f"temp disk usage could not be measured: {error}")
        try:
            shutil.rmtree(run_directory)
        except OSError as error:
            failures.append(f"temp run directory cleanup failed: {error}")

    if failures:
        result["output_validation"] = "failed"
        result["failure_reason"] = "; ".join(dict.fromkeys(failures))
    return result


def _build_report(
    fixture_directory: Path,
    manifest: HMDAEDAFixtureManifest,
    preflight: dict[str, Any],
    runs: list[dict[str, Any]],
    *,
    failure_reason: str | None = None,
) -> dict[str, Any]:
    assessment = (
        {"status": "failed", "reason": failure_reason}
        if failure_reason is not None
        else assess_memory_runs(
            runs,
            process_limit_bytes=PROCESS_LIMIT_BYTES,
            temp_disk_limit_bytes=TEMP_DISK_LIMIT_BYTES,
        )
    )
    return {
        "fixture": hmda_eda_fixture_provenance(fixture_directory, manifest),
        "resources": {
            "process_limit_bytes": PROCESS_LIMIT_BYTES,
            "swap_limit_bytes": 0,
            "duckdb_limit": DUCKDB_LIMIT,
            "duckdb_threads": DUCKDB_THREADS,
            "timeout": TIMEOUT,
            "temp_disk_limit_bytes": TEMP_DISK_LIMIT_BYTES,
        },
        "preflight": preflight,
        "runs": runs,
        "assessment": assessment,
    }


def main() -> int:
    args = parse_args()
    fixture_directory = args.fixture_directory.expanduser().resolve()
    _, manifest = validate_hmda_eda_fixture(fixture_directory)
    preflight: dict[str, Any]
    runs: list[dict[str, Any]] = []
    failure_reason: str | None = None
    try:
        preflight = {"status": "passed", **_verify_hard_limit()}
        for run_number in range(1, 4):
            runs.append(_run_once(fixture_directory, run_number))
    except (OSError, RuntimeError) as error:
        failure_reason = f"memory runner preflight failed: {error}"
        preflight = {"status": "failed", "failure_reason": str(error)}
    report = _build_report(
        fixture_directory,
        manifest,
        preflight,
        runs,
        failure_reason=failure_reason,
    )
    report_path = args.report_path.expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_report_path = report_path.with_suffix(".tmp")
    temporary_report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_report_path.replace(report_path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return (
        0 if report["assessment"]["status"] in {"passed", "improvement_needed"} else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
