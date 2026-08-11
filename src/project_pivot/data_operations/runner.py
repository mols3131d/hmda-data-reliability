"""Raw load와 dbt build/promotion의 application execution boundary.

dbt build가 생성한 artifact는 run-scoped candidate에 남으며 shared current
artifact projection은 자동으로 바꾸지 않는다. Current projection 변경은 caller가
검증을 마친 뒤 ``promote_dbt_artifacts()``를 명시적으로 호출할 때만 일어난다.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from subprocess import CompletedProcess

from project_pivot.data_operations.dbt_result import DbtBuildResult
from project_pivot.data_operations.errors import DataOperationError
from project_pivot.data_operations.incident_lifecycle import (
    run_incident_lifecycle as run_incident_lifecycle,
)
from project_pivot.data_operations.raw_result import RawLoadResult
from project_pivot.data_operations.request import DataOperationRequest
from project_pivot.data_platform.artifacts import (
    ArtifactProjectionLockError,
    ArtifactProjectionReadError,
    artifact_projection_id,
    artifact_projection_lock,
)
from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.hmda_data import discover_hmda_files, load_hmda_loans_partition

_DBT_BUILD_TIMEOUT_SECONDS = 300


def load_raw_data(request: DataOperationRequest) -> RawLoadResult:
    """원천 파일을 DuckDB raw table로 멱등 적재한다.

    같은 partition의 재실행 의미와 중복 방지는 ``hmda_data`` ingestion contract에
    위임하며, 이 함수는 request를 해당 domain API와 result contract로 연결한다.
    """

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
    """dbt build를 고유 run target에서 실행하고 candidate artifact를 반환한다.

    성공해도 shared current artifact projection은 변경하지 않는다. Caller는 이
    결과에 필요한 downstream validation을 끝낸 뒤 ``promote_dbt_artifacts()``를
    별도로 호출해야 한다.
    """

    run_target_path = _create_run_target(request.dbt_run_target_path)
    command = _build_dbt_command(request, run_target_path)
    result = _run_dbt_command(command, request, run_target_path)
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
                "run_target_path": str(run_target_path),
                "stderr": result.stderr,
            },
        )
    manifest_path, run_results_path = _run_artifact_paths(run_target_path)
    _validate_dbt_artifacts(manifest_path, run_results_path)
    try:
        projection_id = artifact_projection_id(manifest_path, run_results_path)
    except ArtifactProjectionReadError as exc:
        raise _artifact_read_error(run_target_path, exc) from exc
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
    """Caller가 검증한 successful run을 current artifact projection으로 승격한다.

    Build 때 계산한 ``projection_id``와 현재 candidate bytes가 일치하는지 다시
    확인하므로, 검증 뒤 변경된 stale result는 승격하지 않는다. Promotion 중
    file operation이 실패하면 기존 current pair 복구를 시도한다.
    """

    if not result.succeeded:
        raise DataOperationError("실패한 dbt run artifact는 승격할 수 없습니다.")
    try:
        with artifact_projection_lock(
            request.dbt_manifest_path.parent,
            exclusive=True,
        ):
            _ensure_artifact_projection(result)
            _promote_dbt_artifacts(
                result.manifest_path,
                result.run_results_path,
                request.dbt_manifest_path,
                request.dbt_run_results_path,
            )
    except ArtifactProjectionLockError as exc:
        raise DataOperationError(
            "dbt artifact projection lock을 획득할 수 없습니다.",
            context={
                "directory": str(request.dbt_manifest_path.parent),
                "run_target_path": str(result.manifest_path.parent),
            },
        ) from exc
    except ArtifactProjectionReadError as exc:
        raise _artifact_read_error(result.manifest_path.parent, exc) from exc


def _build_dbt_command(
    request: DataOperationRequest,
    run_target_path: Path | None = None,
) -> list[str]:
    """dbt build 커맨드 리스트를 생성합니다."""
    target_path = run_target_path or request.dbt_run_target_path
    return [
        "dbt",
        "build",
        "--project-dir",
        str(request.dbt_project_dir),
        "--profiles-dir",
        str(request.dbt_profiles_dir),
        "--target-path",
        str(target_path),
    ]


def _run_dbt_command(
    command: list[str],
    request: DataOperationRequest,
    run_target_path: Path,
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
                "run_target_path": str(run_target_path),
                "timeout_seconds": _DBT_BUILD_TIMEOUT_SECONDS,
            },
        ) from exc
    except OSError as exc:
        msg = "dbt build 프로세스를 시작할 수 없습니다."
        raise DataOperationError(
            msg,
            context={
                "command": command,
                "run_target_path": str(run_target_path),
                "os_error": str(exc),
            },
        ) from exc


def _create_run_target(target_root: Path) -> Path:
    """각 dbt build가 이전/current artifact와 섞이지 않는 고유 target을 만든다."""

    try:
        target_root.mkdir(parents=True, exist_ok=True)
        return Path(tempfile.mkdtemp(prefix="run-", dir=target_root))
    except OSError as exc:
        msg = f"dbt run target을 준비할 수 없습니다: {target_root}"
        raise DataOperationError(msg) from exc


def _run_artifact_paths(run_target_path: Path) -> tuple[Path, Path]:
    return (
        run_target_path / "manifest.json",
        run_target_path / "run_results.json",
    )


def _validate_dbt_artifacts(manifest_path: Path, run_results_path: Path) -> None:
    invalid_paths = [
        path for path in (manifest_path, run_results_path) if not path.is_file()
    ]
    if invalid_paths:
        joined_paths = ", ".join(str(path) for path in invalid_paths)
        msg = f"dbt build artifact를 확인할 수 없습니다: {joined_paths}"
        raise DataOperationError(
            msg,
            context={
                "run_target_path": str(manifest_path.parent),
                "invalid_artifact_paths": [str(path) for path in invalid_paths],
            },
        )


def _ensure_artifact_projection(result: DbtBuildResult) -> None:
    """Promotion 직전 candidate가 build 때 검증한 artifact pair인지 확인한다."""

    _validate_dbt_artifacts(result.manifest_path, result.run_results_path)
    if (
        artifact_projection_id(result.manifest_path, result.run_results_path)
        != result.projection_id
    ):
        raise DataOperationError(
            "dbt artifact projection이 검증 결과와 다릅니다.",
            context={"run_target_path": str(result.manifest_path.parent)},
        )


def _artifact_read_error(
    run_target_path: Path,
    error: ArtifactProjectionReadError,
) -> DataOperationError:
    return DataOperationError(
        "dbt artifact를 읽을 수 없습니다.",
        context={
            "run_target_path": str(run_target_path),
            "artifact_path": str(error.artifact_path),
        },
    )


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
        # Current를 직접 덮어쓰지 않고 두 candidate copy를 먼저 준비한다.
        # Copy 단계 실패가 기존 current pair를 일부만 변경하지 않게 하기 위함이다.
        for source, destination in destinations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(f"{destination.suffix}.next")
            shutil.copyfile(source, temporary)
            temporary_paths.append((temporary, destination))
        # 기존 current를 backup한 뒤 교체해 중간 실패 시 rollback 경로를 남긴다.
        for temporary, destination in temporary_paths:
            backup = destination.with_suffix(f"{destination.suffix}.previous")
            backup.unlink(missing_ok=True)
            if destination.exists():
                destination.replace(backup)
                backup_paths.append((backup, destination))
            temporary.replace(destination)
            promoted_destinations.append(destination)
    except OSError as exc:
        for temporary, _ in temporary_paths:
            temporary.unlink(missing_ok=True)
        for destination in promoted_destinations:
            destination.unlink(missing_ok=True)
        for backup, destination in reversed(backup_paths):
            backup.replace(destination)
        raise DataOperationError(
            "dbt artifact projection을 승격할 수 없습니다.",
            context={"run_target_path": str(run_manifest_path.parent)},
        ) from exc
    # 승격은 이미 완료되었으므로 backup cleanup 실패가 성공 결과를 뒤집지 않게 한다.
    for backup, _ in backup_paths:
        try:
            backup.unlink(missing_ok=True)
        except OSError:
            continue
