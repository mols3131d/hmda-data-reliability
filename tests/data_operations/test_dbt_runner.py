"""dbt 작업 runner 경계 테스트."""

import subprocess
import threading
from contextlib import contextmanager
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired

import pytest

import hmda_reliability.data_platform.artifacts as artifacts
from hmda_reliability.data_operations import (
    data_operation_request_from_environment,
    runner,
)
from hmda_reliability.data_operations.errors import DataOperationError
from hmda_reliability.data_operations.request import DataOperationRequest
from hmda_reliability.data_platform.artifacts import (
    artifact_projection_id,
    artifact_projection_lock,
)
from hmda_reliability.data_platform.duckdb import DuckDBMutationLockError


@pytest.mark.unit
def test_request_from_environment_applies_pipeline_overrides() -> None:
    """공개 pipeline environment 설정을 execution request로 변환한다."""

    request = data_operation_request_from_environment(
        {
            "HMDA_RELIABILITY_DUCKDB_PATH": "scratch/test.duckdb",
            "HMDA_RELIABILITY_SOURCE_ROOT": "scratch/hmda",
            "HMDA_RELIABILITY_SOURCE_YEAR": "2024",
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
        data_operation_request_from_environment({"HMDA_RELIABILITY_SOURCE_YEAR": "next"})


@pytest.mark.unit
@pytest.mark.parametrize(
    ("key", "field"),
    [
        ("HMDA_RELIABILITY_DUCKDB_PATH", "database_path"),
        ("HMDA_RELIABILITY_SOURCE_ROOT", "source_root"),
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

    with pytest.raises(DataOperationError, match="artifact") as error:
        runner.run_dbt_build(_request(tmp_path))

    assert (
        Path(error.value.context["run_target_path"]).parent
        == _request(tmp_path).dbt_run_target_path
    )
    assert error.value.context["invalid_artifact_paths"]


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
    assert (
        Path(error.value.context["run_target_path"]).parent
        == _request(tmp_path).dbt_run_target_path
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
    assert (
        Path(error.value.context["run_target_path"]).parent
        == _request(tmp_path).dbt_run_target_path
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
    """Run target root 생성 실패는 dbt 실행 전에 중단한다."""

    request = _request(tmp_path)

    def fail_mkdir(*args: object, **kwargs: object) -> None:
        raise OSError("cannot create run target")

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)

    with pytest.raises(DataOperationError, match="준비"):
        runner.run_dbt_build(request)


@pytest.mark.component
def test_run_dbt_build_returns_verified_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """이번 실행에서 생성된 artifact만 성공 결과로 반환한다."""

    request = _request(tmp_path)

    def write_artifacts(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        run_target = Path(command[-1])
        run_target.joinpath("manifest.json").write_text(
            '{"run": "current"}', encoding="utf-8"
        )
        run_target.joinpath("run_results.json").write_text(
            '{"run": "current"}', encoding="utf-8"
        )
        return CompletedProcess(["dbt", "build"], 0, "", "")

    monkeypatch.setattr(subprocess, "run", write_artifacts)

    result = runner.run_dbt_build(request)

    assert result.succeeded
    assert result.manifest_path.parent.parent == request.dbt_run_target_path
    assert result.run_results_path.parent == result.manifest_path.parent
    assert result.projection_id.startswith("sha256:")
    assert not request.dbt_manifest_path.exists()
    runner.promote_dbt_artifacts(result, request)
    assert request.dbt_manifest_path.read_text(encoding="utf-8") == '{"run": "current"}'
    assert (
        request.dbt_run_results_path.read_text(encoding="utf-8") == '{"run": "current"}'
    )


@pytest.mark.component
def test_run_dbt_build_holds_database_mutation_lock_during_process(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """dbt subprocess는 target database mutation lock 안에서 실행된다."""

    request = _request(tmp_path)
    lock_held = False

    @contextmanager
    def observe_lock(database_path: str | Path | None):
        nonlocal lock_held
        assert Path(database_path or "") == request.database_path
        lock_held = True
        try:
            yield
        finally:
            lock_held = False

    def write_artifacts(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        assert lock_held
        run_target = Path(command[-1])
        run_target.joinpath("manifest.json").write_text("manifest", encoding="utf-8")
        run_target.joinpath("run_results.json").write_text("results", encoding="utf-8")
        return CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(runner, "database_mutation_lock", observe_lock, raising=False)
    monkeypatch.setattr(subprocess, "run", write_artifacts)

    result = runner.run_dbt_build(request)

    assert result.succeeded
    assert not lock_held


@pytest.mark.component
def test_run_dbt_build_does_not_start_process_when_mutation_lock_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Mutation lock failure는 dbt process 시작 전에 domain error로 변환된다."""

    request = _request(tmp_path)
    process_started = False

    @contextmanager
    def fail_lock(database_path: str | Path | None):
        del database_path
        raise DuckDBMutationLockError("cannot acquire mutation lock")
        yield

    def fail_if_started(*args: object, **kwargs: object) -> CompletedProcess[str]:
        nonlocal process_started
        process_started = True
        raise AssertionError("dbt process must not start")

    monkeypatch.setattr(runner, "database_mutation_lock", fail_lock, raising=False)
    monkeypatch.setattr(subprocess, "run", fail_if_started)

    with pytest.raises(DataOperationError, match="mutation lock") as error:
        runner.run_dbt_build(request)

    assert not process_started
    assert error.value.context["database_path"] == str(request.database_path)


@pytest.mark.component
def test_run_dbt_build_wraps_artifact_byte_read_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Build artifact read I/O failure는 run과 artifact를 식별하는 domain error다."""

    request = _request(tmp_path)
    request.dbt_manifest_path.write_text("last-known-good-manifest", encoding="utf-8")
    request.dbt_run_results_path.write_text("last-known-good-results", encoding="utf-8")
    original_read_bytes = Path.read_bytes
    failed_artifact_path: Path | None = None

    def write_artifacts(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        run_target = Path(command[-1])
        run_target.joinpath("manifest.json").write_text("manifest", encoding="utf-8")
        run_target.joinpath("run_results.json").write_text("results", encoding="utf-8")
        return CompletedProcess(command, 0, "", "")

    def fail_run_manifest_read(path: Path) -> bytes:
        nonlocal failed_artifact_path
        if path.name == "manifest.json" and request.dbt_run_target_path in path.parents:
            failed_artifact_path = path
            raise OSError("artifact bytes unavailable")
        return original_read_bytes(path)

    monkeypatch.setattr(subprocess, "run", write_artifacts)
    monkeypatch.setattr(Path, "read_bytes", fail_run_manifest_read)

    with pytest.raises(DataOperationError, match="artifact") as error:
        runner.run_dbt_build(request)

    assert failed_artifact_path is not None
    assert error.value.context["run_target_path"] == str(failed_artifact_path.parent)
    assert error.value.context["artifact_path"] == str(failed_artifact_path)
    assert request.dbt_manifest_path.read_text(encoding="utf-8") == (
        "last-known-good-manifest"
    )
    assert request.dbt_run_results_path.read_text(encoding="utf-8") == (
        "last-known-good-results"
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

    def write_artifacts(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        run_target = Path(command[-1])
        run_target.joinpath("manifest.json").write_text("candidate", encoding="utf-8")
        run_target.joinpath("run_results.json").write_text(
            "candidate", encoding="utf-8"
        )
        return CompletedProcess(["dbt", "build"], 0, "", "")

    monkeypatch.setattr(subprocess, "run", write_artifacts)

    result = runner.run_dbt_build(request)

    assert result.manifest_path.read_text(encoding="utf-8") == "candidate"
    assert request.dbt_manifest_path.read_text(encoding="utf-8") == "last-known-good"
    assert request.dbt_run_results_path.read_text(encoding="utf-8") == "last-known-good"


@pytest.mark.component
def test_promotion_uses_the_verified_run_artifacts_after_a_later_run(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A 결과는 B 실행 뒤에도 A bytes를 current projection으로 승격한다."""

    request = _request(tmp_path)
    run_number = 0

    def write_artifacts(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        nonlocal run_number
        run_number += 1
        run_target = Path(command[-1])
        run_target.joinpath("manifest.json").write_text(
            f"manifest-{run_number}", encoding="utf-8"
        )
        run_target.joinpath("run_results.json").write_text(
            f"results-{run_number}", encoding="utf-8"
        )
        return CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", write_artifacts)

    first_result = runner.run_dbt_build(request)
    second_result = runner.run_dbt_build(request)
    runner.promote_dbt_artifacts(first_result, request)

    assert first_result.manifest_path != second_result.manifest_path
    assert request.dbt_manifest_path.read_text(encoding="utf-8") == "manifest-1"
    assert request.dbt_run_results_path.read_text(encoding="utf-8") == "results-1"


@pytest.mark.component
def test_promotion_rejects_artifacts_changed_after_verification(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """검증 뒤 artifact bytes가 바뀌면 stale result를 승격하지 않는다."""

    request = _request(tmp_path)

    def write_artifacts(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        run_target = Path(command[-1])
        run_target.joinpath("manifest.json").write_text("manifest", encoding="utf-8")
        run_target.joinpath("run_results.json").write_text("results", encoding="utf-8")
        return CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", write_artifacts)
    result = runner.run_dbt_build(request)
    result.manifest_path.write_text("changed", encoding="utf-8")

    with pytest.raises(DataOperationError, match="projection"):
        runner.promote_dbt_artifacts(result, request)

    assert not request.dbt_manifest_path.exists()
    assert not request.dbt_run_results_path.exists()


@pytest.mark.component
def test_promotion_wraps_artifact_byte_read_failure_and_preserves_current(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Promotion read I/O failure는 raw OSError 없이 current pair를 보존한다."""

    request = _request(tmp_path)
    request.dbt_manifest_path.write_text("old-manifest", encoding="utf-8")
    request.dbt_run_results_path.write_text("old-results", encoding="utf-8")
    run_target = tmp_path / "verified-run"
    run_target.mkdir()
    manifest_path = run_target / "manifest.json"
    run_results_path = run_target / "run_results.json"
    manifest_path.write_text("new-manifest", encoding="utf-8")
    run_results_path.write_text("new-results", encoding="utf-8")
    result = _build_result(manifest_path, run_results_path)
    original_read_bytes = Path.read_bytes

    def fail_verified_manifest_read(path: Path) -> bytes:
        if path == manifest_path:
            raise OSError("artifact bytes unavailable")
        return original_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", fail_verified_manifest_read)

    with pytest.raises(DataOperationError, match="artifact") as error:
        runner.promote_dbt_artifacts(result, request)

    assert error.value.context["run_target_path"] == str(run_target)
    assert error.value.context["artifact_path"] == str(manifest_path)
    assert request.dbt_manifest_path.read_text(encoding="utf-8") == "old-manifest"
    assert request.dbt_run_results_path.read_text(encoding="utf-8") == "old-results"


@pytest.mark.component
def test_promotion_rejects_pair_boundary_collision(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """개별 artifact 경계를 바꾼 동일 concatenation bytes는 승격하지 않는다."""

    request = _request(tmp_path)

    def write_artifacts(command: list[str], **kwargs: object) -> CompletedProcess[str]:
        run_target = Path(command[-1])
        run_target.joinpath("manifest.json").write_text("{} ", encoding="utf-8")
        run_target.joinpath("run_results.json").write_text("{}", encoding="utf-8")
        return CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(subprocess, "run", write_artifacts)
    result = runner.run_dbt_build(request)
    result.manifest_path.write_text("{}", encoding="utf-8")
    result.run_results_path.write_text(" {}", encoding="utf-8")

    with pytest.raises(DataOperationError, match="projection"):
        runner.promote_dbt_artifacts(result, request)

    assert not request.dbt_manifest_path.exists()
    assert not request.dbt_run_results_path.exists()


@pytest.mark.component
def test_concurrent_promotions_do_not_cross_artifact_pairs(tmp_path: Path) -> None:
    """동시 promotion은 manifest/run-results를 서로 다른 run으로 섞지 않는다."""

    request = _request(tmp_path)
    first_run = tmp_path / "first-run"
    second_run = tmp_path / "second-run"
    first_run.mkdir()
    second_run.mkdir()
    first_manifest = first_run / "manifest.json"
    first_results = first_run / "run_results.json"
    second_manifest = second_run / "manifest.json"
    second_results = second_run / "run_results.json"
    first_manifest.write_text("manifest-first", encoding="utf-8")
    first_results.write_text("results-first", encoding="utf-8")
    second_manifest.write_text("manifest-second", encoding="utf-8")
    second_results.write_text("results-second", encoding="utf-8")
    first_result = _build_result(first_manifest, first_results)
    second_result = _build_result(second_manifest, second_results)
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def promote(result: runner.DbtBuildResult) -> None:
        try:
            barrier.wait()
            runner.promote_dbt_artifacts(result, request)
        except BaseException as exc:
            errors.append(exc)

    first_thread = threading.Thread(target=promote, args=(first_result,))
    second_thread = threading.Thread(target=promote, args=(second_result,))
    first_thread.start()
    second_thread.start()
    first_thread.join()
    second_thread.join()

    assert errors == []
    current_pair = (
        request.dbt_manifest_path.read_text(encoding="utf-8"),
        request.dbt_run_results_path.read_text(encoding="utf-8"),
    )
    assert current_pair in {
        ("manifest-first", "results-first"),
        ("manifest-second", "results-second"),
    }


@pytest.mark.component
def test_promotion_rechecks_artifacts_after_waiting_for_lock(tmp_path: Path) -> None:
    """Lock 대기 중 검증 artifact가 바뀌면 promotion은 거부한다."""

    request = _request(tmp_path)
    run_target = tmp_path / "run"
    run_target.mkdir()
    manifest_path = run_target / "manifest.json"
    run_results_path = run_target / "run_results.json"
    manifest_path.write_text("manifest", encoding="utf-8")
    run_results_path.write_text("results", encoding="utf-8")
    result = _build_result(manifest_path, run_results_path)
    promotion_started = threading.Event()
    errors: list[BaseException] = []

    def promote() -> None:
        promotion_started.set()
        try:
            runner.promote_dbt_artifacts(result, request)
        except BaseException as exc:
            errors.append(exc)

    with artifact_projection_lock(request.dbt_manifest_path.parent, exclusive=True):
        thread = threading.Thread(target=promote)
        thread.start()
        assert promotion_started.wait(timeout=1)
        manifest_path.write_text("changed", encoding="utf-8")
    thread.join()

    assert len(errors) == 1
    assert isinstance(errors[0], DataOperationError)
    assert not request.dbt_manifest_path.exists()
    assert not request.dbt_run_results_path.exists()


@pytest.mark.component
def test_promotion_lock_failure_preserves_failed_run_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Promotion lock 실패도 verified run artifact 위치를 보존한다."""

    request = _request(tmp_path)
    run_target = tmp_path / "run"
    run_target.mkdir()
    manifest_path = run_target / "manifest.json"
    run_results_path = run_target / "run_results.json"
    manifest_path.write_text("manifest", encoding="utf-8")
    run_results_path.write_text("results", encoding="utf-8")

    def fail_lock(*args: object, **kwargs: object) -> None:
        raise runner.ArtifactProjectionLockError("lock failed")

    monkeypatch.setattr(runner, "artifact_projection_lock", fail_lock)

    with pytest.raises(DataOperationError, match="lock") as error:
        runner.promote_dbt_artifacts(
            _build_result(manifest_path, run_results_path),
            request,
        )

    assert error.value.context["run_target_path"] == str(run_target)


@pytest.mark.component
def test_promotion_release_failure_reports_committed_current_pair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Commit 뒤 lock release failure는 promoted pair와 domain error를 함께 보존한다."""

    request = _request(tmp_path)
    request.dbt_manifest_path.write_text("old-manifest", encoding="utf-8")
    request.dbt_run_results_path.write_text("old-results", encoding="utf-8")
    run_target = tmp_path / "run"
    run_target.mkdir()
    manifest_path = run_target / "manifest.json"
    run_results_path = run_target / "run_results.json"
    manifest_path.write_text("new-manifest", encoding="utf-8")
    run_results_path.write_text("new-results", encoding="utf-8")
    result = _build_result(manifest_path, run_results_path)
    original_flock = artifacts.fcntl.flock

    def fail_unlock(file_descriptor: int, operation: int) -> None:
        if operation == artifacts.fcntl.LOCK_UN:
            raise OSError("cannot release artifact lock")
        original_flock(file_descriptor, operation)

    monkeypatch.setattr(artifacts.fcntl, "flock", fail_unlock)

    with pytest.raises(DataOperationError, match="lock") as error:
        runner.promote_dbt_artifacts(result, request)

    assert error.value.context["run_target_path"] == str(run_target)
    assert request.dbt_manifest_path.read_text(encoding="utf-8") == "new-manifest"
    assert request.dbt_run_results_path.read_text(encoding="utf-8") == "new-results"


@pytest.mark.component
def test_artifact_promotion_restores_pair_when_second_replace_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Partial promotion failure는 last-known-good artifact pair를 복구한다."""

    request = _request(tmp_path)
    request.dbt_manifest_path.write_text("old-manifest", encoding="utf-8")
    request.dbt_run_results_path.write_text("old-results", encoding="utf-8")
    run_target = tmp_path / "run"
    run_target.mkdir()
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


@pytest.mark.component
def test_artifact_backup_cleanup_failure_preserves_committed_pair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Commit 뒤 backup cleanup 오류는 current artifact pair를 rollback하지 않는다."""

    request = _request(tmp_path)
    request.dbt_manifest_path.write_text("old-manifest", encoding="utf-8")
    request.dbt_run_results_path.write_text("old-results", encoding="utf-8")
    run_target = tmp_path / "run"
    run_target.mkdir()
    run_manifest = run_target / "manifest.json"
    run_results = run_target / "run_results.json"
    run_manifest.write_text("new-manifest", encoding="utf-8")
    run_results.write_text("new-results", encoding="utf-8")
    original_unlink = Path.unlink
    cleanup_count = 0

    def fail_second_cleanup(path: Path, missing_ok: bool = False) -> None:
        nonlocal cleanup_count
        if path.suffix == ".previous":
            cleanup_count += 1
            if cleanup_count == 4:
                raise OSError("simulated cleanup failure")
        original_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", fail_second_cleanup)

    runner._promote_dbt_artifacts(
        run_manifest,
        run_results,
        request.dbt_manifest_path,
        request.dbt_run_results_path,
    )

    assert request.dbt_manifest_path.read_text(encoding="utf-8") == "new-manifest"
    assert request.dbt_run_results_path.read_text(encoding="utf-8") == "new-results"


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


def _build_result(manifest_path: Path, run_results_path: Path):
    return runner.DbtBuildResult(
        command=["dbt", "build"],
        return_code=0,
        manifest_path=manifest_path,
        run_results_path=run_results_path,
        projection_id=artifact_projection_id(manifest_path, run_results_path),
        succeeded=True,
    )
