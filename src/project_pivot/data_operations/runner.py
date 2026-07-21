"""데이터 적재와 dbt build를 실행한다."""

from __future__ import annotations

import os
import subprocess

from project_pivot.data_operations.dbt_result import DbtBuildResult
from project_pivot.data_operations.errors import DataOperationError
from project_pivot.data_operations.incident_lifecycle import (
    run_incident_lifecycle as run_incident_lifecycle,
)
from project_pivot.data_operations.raw_result import RawLoadResult
from project_pivot.data_operations.request import DataOperationRequest
from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import discover_hmda_files, load_hmda_loans_partition

_DBT_BUILD_TIMEOUT_SECONDS = 300


def load_raw_data(request: DataOperationRequest) -> RawLoadResult:
    """원천 파일을 DuckDB raw table로 멱등 적재한다."""

    hmda_paths = discover_hmda_files(request.source_root)
    with DuckDBConnectionManager(request.database_path) as connection:
        hmda_loans_row_count = load_hmda_loans_partition(
            connection,
            hmda_paths,
            request.source_year,
            source_file=request.source_file,
            table_name=request.raw_table_name,
        )
    return RawLoadResult(
        database_path=request.database_path,
        source_root=request.source_root,
        source_file_count=len(hmda_paths),
        source_year=request.source_year,
        source_file=request.source_file,
        hmda_loans_row_count=hmda_loans_row_count,
    )


def run_dbt_build(request: DataOperationRequest) -> DbtBuildResult:
    """dbt build를 실행하고 artifact 경로를 반환한다."""

    command = [
        "dbt",
        "build",
        "--project-dir",
        str(request.dbt_project_dir),
        "--profiles-dir",
        str(request.dbt_profiles_dir),
    ]
    env = os.environ.copy()
    env["PROJECT_PIVOT_DUCKDB_PATH"] = str(request.database_path)
    env["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    _remove_dbt_artifacts(request)
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            env=env,
            text=True,
            timeout=_DBT_BUILD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"dbt build 실행 시간이 {_DBT_BUILD_TIMEOUT_SECONDS}초를 초과했습니다."
        raise DataOperationError(msg) from exc
    except OSError as exc:
        msg = "dbt build 프로세스를 시작할 수 없습니다."
        raise DataOperationError(msg) from exc
    if result.returncode != 0:
        stderr_lines = result.stderr.strip().splitlines()
        stderr = stderr_lines[-1][:500] if stderr_lines else "출력 없음"
        msg = (
            "dbt build 실행에 실패했습니다: "
            f"return_code={result.returncode}, stderr={stderr}"
        )
        raise DataOperationError(msg)
    _validate_dbt_artifacts(request)
    return DbtBuildResult(
        command=command,
        return_code=result.returncode,
        manifest_path=request.dbt_manifest_path,
        run_results_path=request.dbt_run_results_path,
        succeeded=True,
    )


def _remove_dbt_artifacts(request: DataOperationRequest) -> None:
    for path in (request.dbt_manifest_path, request.dbt_run_results_path):
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            msg = f"기존 dbt artifact를 제거할 수 없습니다: {path}"
            raise DataOperationError(msg) from exc


def _validate_dbt_artifacts(request: DataOperationRequest) -> None:
    invalid_paths = [
        path
        for path in (request.dbt_manifest_path, request.dbt_run_results_path)
        if not path.is_file()
    ]
    if invalid_paths:
        joined_paths = ", ".join(str(path) for path in invalid_paths)
        msg = f"dbt build artifact를 확인할 수 없습니다: {joined_paths}"
        raise DataOperationError(msg)
