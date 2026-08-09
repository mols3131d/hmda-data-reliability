"""dbt 작업 runner 경계 테스트."""

import shutil
import subprocess
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired

import pytest

from project_pivot.data_operations import (
    data_operation_request_from_environment,
    runner,
)
from project_pivot.data_operations.errors import DataOperationError
from project_pivot.data_operations.request import DataOperationRequest


@pytest.mark.unit
def test_request_from_environment_applies_pipeline_overrides() -> None:
    """공개 pipeline environment 설정을 execution request로 변환한다."""

    request = data_operation_request_from_environment(
        {
            "PROJECT_PIVOT_DUCKDB_PATH": "scratch/test.duckdb",
            "PROJECT_PIVOT_SOURCE_ROOT": "scratch/hmda",
            "PROJECT_PIVOT_SOURCE_YEAR": "2024",
        }
    )

    assert request.database_path == Path("scratch/test.duckdb")
    assert request.source_root == Path("scratch/hmda")
    assert request.source_year == 2024


@pytest.mark.unit
def test_request_from_environment_preserves_local_defaults() -> None:
    """설정되지 않은 environment는 기존 로컬 실행 기본값을 유지한다."""

    assert data_operation_request_from_environment({}) == DataOperationRequest()


@pytest.mark.unit
def test_request_from_environment_rejects_invalid_source_year() -> None:
    """정수가 아닌 source year는 request validation error로 노출한다."""

    with pytest.raises(ValueError, match="source_year"):
        data_operation_request_from_environment({"PROJECT_PIVOT_SOURCE_YEAR": "next"})


@pytest.mark.unit
@pytest.mark.parametrize(
    ("key", "field"),
    [
        ("PROJECT_PIVOT_DUCKDB_PATH", "database_path"),
        ("PROJECT_PIVOT_SOURCE_ROOT", "source_root"),
    ],
)
def test_request_from_environment_rejects_empty_paths(key: str, field: str) -> None:
    """빈 pipeline path는 fallback하지 않고 request validation error로 노출한다."""

    with pytest.raises(ValueError, match=field):
        data_operation_request_from_environment({key: ""})


@pytest.mark.component
def test_run_dbt_build_requires_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """종료 코드 0이어도 artifact가 없으면 실패한다."""

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args[0], 0, "", ""),
    )

    with pytest.raises(DataOperationError, match="artifact"):
        runner.run_dbt_build(_request(tmp_path))


@pytest.mark.component
def test_run_dbt_build_wraps_timeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """dbt 제한 시간 초과를 데이터 작업 오류로 변환한다."""

    def raise_timeout(*args: object, **kwargs: object) -> CompletedProcess[str]:
        raise TimeoutExpired(cmd="dbt build", timeout=300)

    monkeypatch.setattr(subprocess, "run", raise_timeout)

    with pytest.raises(DataOperationError, match="시간") as error:
        runner.run_dbt_build(_request(tmp_path))

    assert error.value.context["command"][0:2] == ["dbt", "build"]
    assert error.value.context["run_target_path"] == str(
        _request(tmp_path).dbt_run_target_path
    )


@pytest.mark.component
def test_run_dbt_build_includes_last_stderr_line(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """dbt 실패 원인의 마지막 줄을 데이터 작업 오류에 포함한다."""

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(
            args[0],
            1,
            "",
            "상세 stack trace\nprofiles.yml을 찾을 수 없습니다.",
        ),
    )

    with pytest.raises(
        DataOperationError, match="profiles.yml을 찾을 수 없습니다"
    ) as error:
        runner.run_dbt_build(_request(tmp_path))

    assert error.value.context["return_code"] == 1
    assert error.value.context["run_target_path"] == str(
        _request(tmp_path).dbt_run_target_path
    )
    assert error.value.context["command"][0:2] == ["dbt", "build"]


@pytest.mark.component
def test_run_dbt_build_rejects_preexisting_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """이전 current artifact를 이번 실행 결과로 인정하거나 삭제하지 않는다."""

    request = _request(tmp_path)
    request.dbt_manifest_path.write_text("stale", encoding="utf-8")
    request.dbt_run_results_path.write_text("stale", encoding="utf-8")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args[0], 0, "", ""),
    )

    with pytest.raises(DataOperationError, match="artifact"):
        runner.run_dbt_build(request)

    assert request.dbt_manifest_path.read_text(encoding="utf-8") == "stale"
    assert request.dbt_run_results_path.read_text(encoding="utf-8") == "stale"


@pytest.mark.component
def test_run_dbt_build_fails_when_run_target_cannot_be_cleared(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Run target cleanup failure는 stale artifact 사용 전에 중단한다."""

    request = _request(tmp_path)
    request.dbt_run_target_path.mkdir(parents=True)
    (request.dbt_run_target_path / "manifest.json").write_text(
        "stale", encoding="utf-8"
    )

    def fail_cleanup(path: Path) -> None:
        raise OSError(f"cannot remove {path}")

    monkeypatch.setattr(shutil, "rmtree", fail_cleanup)

    with pytest.raises(DataOperationError, match="준비"):
        runner.run_dbt_build(request)


@pytest.mark.component
def test_run_dbt_build_returns_verified_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """이번 실행에서 생성된 artifact만 성공 결과로 반환한다."""

    request = _request(tmp_path)

    def write_artifacts(*args: object, **kwargs: object) -> CompletedProcess[str]:
        (request.dbt_run_target_path / "manifest.json").write_text(
            '{"run": "current"}', encoding="utf-8"
        )
        (request.dbt_run_target_path / "run_results.json").write_text(
            '{"run": "current"}', encoding="utf-8"
        )
        return CompletedProcess(["dbt", "build"], 0, "", "")

    monkeypatch.setattr(subprocess, "run", write_artifacts)

    result = runner.run_dbt_build(request)

    assert result.succeeded
    assert result.manifest_path == request.dbt_run_target_path / "manifest.json"
    assert result.run_results_path == request.dbt_run_target_path / "run_results.json"
    assert result.projection_id.startswith("sha256:")
    assert not request.dbt_manifest_path.exists()
    runner.promote_dbt_artifacts(result, request)
    assert request.dbt_manifest_path.read_text(encoding="utf-8") == '{"run": "current"}'
    assert (
        request.dbt_run_results_path.read_text(encoding="utf-8") == '{"run": "current"}'
    )


@pytest.mark.component
def test_candidate_dbt_build_does_not_promote_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Candidate run artifact는 current projection을 변경하지 않는다."""

    request = _request(tmp_path)
    request.dbt_manifest_path.write_text("last-known-good", encoding="utf-8")
    request.dbt_run_results_path.write_text("last-known-good", encoding="utf-8")

    def write_artifacts(*args: object, **kwargs: object) -> CompletedProcess[str]:
        (request.dbt_run_target_path / "manifest.json").write_text(
            "candidate", encoding="utf-8"
        )
        (request.dbt_run_target_path / "run_results.json").write_text(
            "candidate", encoding="utf-8"
        )
        return CompletedProcess(["dbt", "build"], 0, "", "")

    monkeypatch.setattr(subprocess, "run", write_artifacts)

    result = runner.run_dbt_build(request)

    assert result.manifest_path.read_text(encoding="utf-8") == "candidate"
    assert request.dbt_manifest_path.read_text(encoding="utf-8") == "last-known-good"
    assert request.dbt_run_results_path.read_text(encoding="utf-8") == "last-known-good"


@pytest.mark.component
def test_artifact_promotion_restores_pair_when_second_replace_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Partial promotion failure는 last-known-good artifact pair를 복구한다."""

    request = _request(tmp_path)
    request.dbt_manifest_path.write_text("old-manifest", encoding="utf-8")
    request.dbt_run_results_path.write_text("old-results", encoding="utf-8")
    run_target = request.dbt_run_target_path
    run_target.mkdir(parents=True)
    run_manifest = run_target / "manifest.json"
    run_results = run_target / "run_results.json"
    run_manifest.write_text("new-manifest", encoding="utf-8")
    run_results.write_text("new-results", encoding="utf-8")
    original_replace = Path.replace

    def fail_second_replace(path: Path, target: Path) -> Path:
        if path.name == "run_results.json.next":
            raise OSError("simulated replace failure")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_second_replace)

    with pytest.raises(DataOperationError, match="승격"):
        runner._promote_dbt_artifacts(
            run_manifest,
            run_results,
            request.dbt_manifest_path,
            request.dbt_run_results_path,
        )

    assert request.dbt_manifest_path.read_text(encoding="utf-8") == "old-manifest"
    assert request.dbt_run_results_path.read_text(encoding="utf-8") == "old-results"


@pytest.mark.unit
def test_build_dbt_command_structures_arguments(tmp_path: Path) -> None:
    """dbt build 인자 리스트가 올바른 옵션으로 구성되는지 검증한다."""

    request = _request(tmp_path)
    command = runner._build_dbt_command(request)

    assert command == [
        "dbt",
        "build",
        "--project-dir",
        str(request.dbt_project_dir),
        "--profiles-dir",
        str(request.dbt_profiles_dir),
        "--target-path",
        str(request.dbt_run_target_path),
    ]


def _request(tmp_path: Path) -> DataOperationRequest:
    return DataOperationRequest(
        dbt_manifest_path=tmp_path / "manifest.json",
        dbt_run_results_path=tmp_path / "run_results.json",
        dbt_run_target_path=tmp_path / "runs" / "current",
    )
