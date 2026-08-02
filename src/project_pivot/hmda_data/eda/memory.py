"""HMDA EDA memory workload 실행과 결과 판정."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import duckdb

from project_pivot.hmda_data.eda.analysis import analyze_hmda_csv
from project_pivot.hmda_data.eda.fixture import (
    hmda_eda_fixture_provenance,
    validate_hmda_eda_evidence,
    validate_hmda_eda_fixture,
)


def run_hmda_eda_memory_workload(
    fixture_directory: str | Path,
    *,
    temp_directory: str | Path,
    output_path: str | Path,
    memory_limit: str = "1600MB",
    threads: int = 2,
) -> dict[str, Any]:
    """대표 fixture를 분석하고 invariant 검증 결과를 JSON으로 기록한다."""

    fixture_path, manifest = validate_hmda_eda_fixture(fixture_directory)
    evidence = analyze_hmda_csv(
        fixture_path,
        memory_limit=memory_limit,
        threads=threads,
        temp_directory=temp_directory,
    )
    validate_hmda_eda_evidence(evidence, manifest)
    result = {
        "status": "passed",
        "fixture_version": manifest.version,
        "fixture": hmda_eda_fixture_provenance(fixture_directory, manifest),
        "duckdb_limit": memory_limit,
        "threads": threads,
        "output_validation": "passed",
        "evidence": evidence,
        "environment": {
            "python": sys.version.split()[0],
            "duckdb": duckdb.__version__,
        },
    }
    resolved_output_path = Path(output_path).expanduser().resolve()
    resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_output_path = resolved_output_path.with_suffix(".tmp")
    temporary_output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_output_path.replace(resolved_output_path)
    return result


def parse_gnu_time_report(report: str) -> dict[str, float | int]:
    """GNU time verbose output에서 peak RSS와 elapsed seconds를 추출한다."""

    peak_rss_kib: int | None = None
    elapsed_seconds: float | None = None
    for raw_line in report.splitlines():
        line = raw_line.strip()
        if line.startswith("Maximum resident set size (kbytes):"):
            peak_rss_kib = int(line.rsplit(":", 1)[1].strip())
        elif line.startswith("Elapsed (wall clock) time"):
            elapsed_text = line.split("):", 1)[1].strip()
            parts = [float(part) for part in elapsed_text.split(":")]
            elapsed_seconds = sum(
                value * (60**index) for index, value in enumerate(reversed(parts))
            )
    if peak_rss_kib is None or elapsed_seconds is None:
        raise ValueError("GNU time report is missing peak RSS or elapsed time")
    return {"peak_rss_kib": peak_rss_kib, "elapsed_seconds": elapsed_seconds}


def assess_memory_runs(
    runs: list[dict[str, Any]],
    *,
    process_limit_bytes: int,
    temp_disk_limit_bytes: int,
) -> dict[str, Any]:
    """세 반복의 process 상태와 peak RSS margin을 판정한다."""

    if len(runs) != 3:
        return {"status": "failed", "reason": "exactly three runs are required"}
    failed_runs = [
        run
        for run in runs
        if run.get("exit_code") != 0
        or run.get("output_validation") != "passed"
        or run.get("resource_status") != "passed"
        or run.get("temp_disk_bytes", 0) > temp_disk_limit_bytes
    ]
    if failed_runs:
        return {
            "status": "failed",
            "reason": "process, resource, temp disk, or output validation failed",
            "failed_runs": [run["run"] for run in failed_runs],
        }

    max_peak_rss_bytes = max(run["peak_rss_kib"] for run in runs) * 1024
    peak_ratio = max_peak_rss_bytes / process_limit_bytes
    return {
        "status": "improvement_needed" if peak_ratio > 0.85 else "passed",
        "max_peak_rss_bytes": max_peak_rss_bytes,
        "peak_ratio": peak_ratio,
    }
