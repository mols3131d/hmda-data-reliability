"""데이터 적재와 dbt build를 실행한다."""

from __future__ import annotations

import os
import shutil
import subprocess
from hashlib import sha256
from pathlib import Path
from subprocess import CompletedProcess

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

    command = _build_dbt_command(request)
    _prepare_run_target(request.dbt_run_target_path)
    result = _run_dbt_command(command, request)
    if result.returncode != 0:
        stderr_lines = result.stderr.strip().splitlines()
        stderr = stderr_lines[-1][:500] if stderr_lines else "출력 없음"
        msg = (
            "dbt build 실행에 실패했습니다: "
            f"return_code={result.returncode}, stderr={stderr}"
        )
        raise DataOperationError(
            msg,
            context={
                "command": command,
                "return_code": result.returncode,
                "run_target_path": str(request.dbt_run_target_path),
                "stderr": result.stderr,
            },
        )
    manifest_path, run_results_path = _run_artifact_paths(request)
    _validate_dbt_artifacts(manifest_path, run_results_path)
    projection_id = _artifact_projection_id(manifest_path, run_results_path)
    return DbtBuildResult(
        command=command,
        return_code=result.returncode,
        manifest_path=manifest_path,
        run_results_path=run_results_path,
        projection_id=projection_id,
        succeeded=True,
    )


def promote_dbt_artifacts(
    result: DbtBuildResult,
    request: DataOperationRequest,
) -> None:
    """Promote a caller-validated successful run to the current projection."""

    if not result.succeeded:
        raise DataOperationError("실패한 dbt run artifact는 승격할 수 없습니다.")
    _promote_dbt_artifacts(
        result.manifest_path,
        result.run_results_path,
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )


def _build_dbt_command(request: DataOperationRequest) -> list[str]:
    """dbt build 커맨드 리스트를 생성합니다."""
    return [
        "dbt",
        "build",
        "--project-dir",
        str(request.dbt_project_dir),
        "--profiles-dir",
        str(request.dbt_profiles_dir),
        "--target-path",
        str(request.dbt_run_target_path),
    ]


def _run_dbt_command(
    command: list[str], request: DataOperationRequest
) -> CompletedProcess[str]:
    """dbt build를 실행하고 결과 CompletedProcess를 반환합니다."""
    env = os.environ.copy()
    env["PROJECT_PIVOT_DUCKDB_PATH"] = str(request.database_path)
    env["DBT_SEND_ANONYMOUS_USAGE_STATS"] = "false"
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            env=env,
            text=True,
            timeout=_DBT_BUILD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        msg = f"dbt build 실행 시간이 {_DBT_BUILD_TIMEOUT_SECONDS}초를 초과했습니다."
        raise DataOperationError(
            msg,
            context={
                "command": command,
                "run_target_path": str(request.dbt_run_target_path),
                "timeout_seconds": _DBT_BUILD_TIMEOUT_SECONDS,
            },
        ) from exc
    except OSError as exc:
        msg = "dbt build 프로세스를 시작할 수 없습니다."
        raise DataOperationError(
            msg,
            context={
                "command": command,
                "run_target_path": str(request.dbt_run_target_path),
                "os_error": str(exc),
            },
        ) from exc


def _prepare_run_target(target_path: Path) -> None:
    try:
        if target_path.exists():
            shutil.rmtree(target_path)
        target_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        msg = f"dbt run target을 준비할 수 없습니다: {target_path}"
        raise DataOperationError(msg) from exc


def _run_artifact_paths(request: DataOperationRequest) -> tuple[Path, Path]:
    return (
        request.dbt_run_target_path / "manifest.json",
        request.dbt_run_target_path / "run_results.json",
    )


def _validate_dbt_artifacts(manifest_path: Path, run_results_path: Path) -> None:
    invalid_paths = [
        path for path in (manifest_path, run_results_path) if not path.is_file()
    ]
    if invalid_paths:
        joined_paths = ", ".join(str(path) for path in invalid_paths)
        msg = f"dbt build artifact를 확인할 수 없습니다: {joined_paths}"
        raise DataOperationError(msg)


def _artifact_projection_id(manifest_path: Path, run_results_path: Path) -> str:
    digest = sha256()
    digest.update(manifest_path.read_bytes())
    digest.update(run_results_path.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _promote_dbt_artifacts(
    run_manifest_path: Path,
    run_results_path: Path,
    current_manifest_path: Path,
    current_run_results_path: Path,
) -> None:
    destinations = (
        (run_manifest_path, current_manifest_path),
        (run_results_path, current_run_results_path),
    )
    temporary_paths: list[tuple[Path, Path]] = []
    backup_paths: list[tuple[Path, Path]] = []
    promoted_destinations: list[Path] = []
    try:
        for source, destination in destinations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(f"{destination.suffix}.next")
            shutil.copyfile(source, temporary)
            temporary_paths.append((temporary, destination))
        for temporary, destination in temporary_paths:
            backup = destination.with_suffix(f"{destination.suffix}.previous")
            backup.unlink(missing_ok=True)
            if destination.exists():
                destination.replace(backup)
                backup_paths.append((backup, destination))
            temporary.replace(destination)
            promoted_destinations.append(destination)
        for backup, _ in backup_paths:
            backup.unlink(missing_ok=True)
    except OSError as exc:
        for temporary, _ in temporary_paths:
            temporary.unlink(missing_ok=True)
        for destination in promoted_destinations:
            destination.unlink(missing_ok=True)
        for backup, destination in reversed(backup_paths):
            backup.replace(destination)
        raise DataOperationError(
            "dbt artifact projection을 승격할 수 없습니다."
        ) from exc
