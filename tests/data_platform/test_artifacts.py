"""Artifact pair byte identity와 shared/exclusive projection lock 경계."""

from pathlib import Path

import pytest

import hmda_reliability.data_platform.artifacts as artifacts
from hmda_reliability.data_platform.artifacts import (
    ArtifactProjectionLockError,
    ArtifactProjectionReadError,
    artifact_projection_id,
    artifact_projection_lock,
)


@pytest.mark.component
@pytest.mark.parametrize(
    ("original_pair", "changed_pair"),
    [
        ((b"manifest", b"results"), (b"manifest", b"changed")),
        ((b"manifest", b"results"), (b"changed", b"results")),
        ((b"first", b"second"), (b"second", b"first")),
        ((b"{} ", b"{}"), (b"{}", b" {}")),
    ],
    ids=["results-only", "manifest-only", "ordered-pair", "byte-boundary"],
)
def test_projection_identity_distinguishes_artifact_pairs(
    tmp_path: Path,
    original_pair: tuple[bytes, bytes],
    changed_pair: tuple[bytes, bytes],
) -> None:
    manifest_path = tmp_path / "manifest.json"
    run_results_path = tmp_path / "run_results.json"
    manifest_path.write_bytes(original_pair[0])
    run_results_path.write_bytes(original_pair[1])
    original_identity = artifact_projection_id(manifest_path, run_results_path)

    manifest_path.write_bytes(changed_pair[0])
    run_results_path.write_bytes(changed_pair[1])

    assert artifact_projection_id(manifest_path, run_results_path) != original_identity


@pytest.mark.component
def test_projection_identity_depends_on_bytes_instead_of_paths(tmp_path: Path) -> None:
    """Primitive는 JSON 해석 없이 동일한 opaque bytes를 같은 pair로 식별한다."""

    manifest_path = tmp_path / "manifest.json"
    run_results_path = tmp_path / "run_results.json"
    manifest_path.write_bytes(b"\xff\x00manifest")
    run_results_path.write_bytes(b"")
    original_identity = artifact_projection_id(manifest_path, run_results_path)
    relocated_manifest = manifest_path.rename(tmp_path / "relocated-manifest.json")
    relocated_results = run_results_path.rename(tmp_path / "relocated-results.json")

    relocated_identity = artifact_projection_id(relocated_manifest, relocated_results)

    assert relocated_identity == original_identity


@pytest.mark.component
@pytest.mark.parametrize("missing_name", ["manifest.json", "run_results.json"])
def test_projection_identity_reports_the_unreadable_artifact(
    tmp_path: Path,
    missing_name: str,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    run_results_path = tmp_path / "run_results.json"
    manifest_path.write_bytes(b"manifest")
    run_results_path.write_bytes(b"results")
    missing_path = tmp_path / missing_name
    missing_path.unlink()

    with pytest.raises(ArtifactProjectionReadError) as error:
        artifact_projection_id(manifest_path, run_results_path)

    assert error.value.artifact_path == missing_path
    assert isinstance(error.value.__cause__, FileNotFoundError)


@pytest.mark.component
@pytest.mark.parametrize(
    ("holder_exclusive", "contender_exclusive", "blocked"),
    [
        (False, False, False),
        (False, True, True),
        (True, False, True),
        (True, True, True),
    ],
    ids=["reader-reader", "reader-writer", "writer-reader", "writer-writer"],
)
def test_projection_lock_enforces_shared_and_exclusive_access(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    holder_exclusive: bool,
    contender_exclusive: bool,
    blocked: bool,
) -> None:
    original_flock = artifacts.fcntl.flock

    def nonblocking_flock(file_descriptor: int, operation: int) -> None:
        if operation != artifacts.fcntl.LOCK_UN:
            operation |= artifacts.fcntl.LOCK_NB
        original_flock(file_descriptor, operation)

    with artifact_projection_lock(tmp_path, exclusive=holder_exclusive):
        # 실제 OS lock에 비차단 contender를 연결해 sleep 없이 contention을 관찰한다.
        monkeypatch.setattr(artifacts.fcntl, "flock", nonblocking_flock)
        if blocked:
            with (
                pytest.raises(ArtifactProjectionLockError) as error,
                artifact_projection_lock(tmp_path, exclusive=contender_exclusive),
            ):
                pytest.fail("Conflicting artifact lock entered its body")
            assert isinstance(error.value.__cause__, BlockingIOError)
        else:
            with artifact_projection_lock(tmp_path, exclusive=contender_exclusive):
                pass

    with artifact_projection_lock(tmp_path, exclusive=True):
        pass


@pytest.mark.component
def test_artifact_read_failure_is_not_translated_as_lock_failure(
    tmp_path: Path,
) -> None:
    """Lock 안의 artifact read failure는 원래 오류를 보존한다."""

    with (
        pytest.raises(FileNotFoundError),
        artifact_projection_lock(tmp_path, exclusive=False),
    ):
        (tmp_path / "missing.json").read_bytes()


@pytest.mark.component
def test_artifact_lock_setup_failure_is_translated(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Lock directory setup failure는 typed lock error로 변환한다."""

    def fail_mkdir(*args: object, **kwargs: object) -> None:
        raise OSError("cannot create lock directory")

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)

    with (
        pytest.raises(ArtifactProjectionLockError, match="lock"),
        artifact_projection_lock(tmp_path, exclusive=False),
    ):
        pass


@pytest.mark.component
def test_artifact_lock_release_failure_is_translated(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Lock release I/O failure도 typed lock error로 변환한다."""

    original_flock = artifacts.fcntl.flock

    def fail_unlock(file_descriptor: int, operation: int) -> None:
        if operation == artifacts.fcntl.LOCK_UN:
            raise OSError("cannot release artifact lock")
        original_flock(file_descriptor, operation)

    monkeypatch.setattr(artifacts.fcntl, "flock", fail_unlock)

    with (
        pytest.raises(ArtifactProjectionLockError, match="lock"),
        artifact_projection_lock(tmp_path, exclusive=True),
    ):
        pass


@pytest.mark.component
def test_artifact_body_failure_takes_precedence_over_unlock_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    original_flock = artifacts.fcntl.flock
    body_error = FileNotFoundError("artifact body failed")

    def fail_unlock(file_descriptor: int, operation: int) -> None:
        if operation == artifacts.fcntl.LOCK_UN:
            raise OSError("cannot release artifact lock")
        original_flock(file_descriptor, operation)

    monkeypatch.setattr(artifacts.fcntl, "flock", fail_unlock)

    with (
        pytest.raises(FileNotFoundError) as error,
        artifact_projection_lock(tmp_path, exclusive=False),
    ):
        raise body_error

    assert error.value is body_error
