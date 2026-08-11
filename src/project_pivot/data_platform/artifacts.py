"""dbt artifact projection identity와 local reader/writer lock."""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path


class ArtifactProjectionLockError(Exception):
    """Artifact projection lock I/O에 실패했다."""


class ArtifactProjectionReadError(Exception):
    """Artifact projection byte read에 실패했다."""

    def __init__(self, artifact_path: Path) -> None:
        super().__init__(f"dbt artifact를 읽을 수 없습니다: {artifact_path}")
        self.artifact_path = artifact_path


def artifact_projection_id(manifest_path: Path, run_results_path: Path) -> str:
    """Artifact pair 경계를 보존하는 projection identity를 반환한다."""

    digest = sha256()
    for path in (manifest_path, run_results_path):
        try:
            artifact_bytes = path.read_bytes()
        except OSError as exc:
            raise ArtifactProjectionReadError(path) from exc
        digest.update(len(artifact_bytes).to_bytes(8, byteorder="big"))
        digest.update(artifact_bytes)
    return f"sha256:{digest.hexdigest()}"


@contextmanager
def artifact_projection_lock(directory: Path, *, exclusive: bool) -> Iterator[None]:
    """Current artifact pair의 reader/writer access를 직렬화한다."""

    try:
        directory.mkdir(parents=True, exist_ok=True)
        lock_file = (directory / ".artifact-promotion.lock").open("w")
        mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(lock_file, mode)
    except OSError as exc:
        msg = f"dbt artifact projection lock을 획득할 수 없습니다: {directory}"
        raise ArtifactProjectionLockError(msg) from exc
    body_failed = False
    try:
        yield
    except BaseException:
        body_failed = True
        raise
    finally:
        release_error: OSError | None = None
        try:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
        except OSError as exc:
            release_error = exc
        try:
            lock_file.close()
        except OSError as exc:
            release_error = release_error or exc
        if release_error is not None and not body_failed:
            msg = f"dbt artifact projection lock을 해제할 수 없습니다: {directory}"
            raise ArtifactProjectionLockError(msg) from release_error
