"""Artifact projection lock 경계 테스트."""

from pathlib import Path

import pytest

import hmda_reliability.data_platform.artifacts as artifacts
from hmda_reliability.data_platform.artifacts import (
    ArtifactProjectionLockError,
    artifact_projection_lock,
)


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
