"""dbt artifact pair identity와 current projection의 local lock primitive."""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path


class ArtifactProjectionLockError(Exception):
    """Projection lock의 setup 또는 release I/O 실패를 나타낸다."""


class ArtifactProjectionReadError(Exception):
    """Projection identity 계산 중 artifact byte read 실패를 나타낸다."""

    def __init__(self, artifact_path: Path) -> None:
        super().__init__(f"dbt artifact를 읽을 수 없습니다: {artifact_path}")
        self.artifact_path = artifact_path


def artifact_projection_id(manifest_path: Path, run_results_path: Path) -> str:
    """Ordered artifact bytes에서 pair boundary를 보존한 identity를 계산한다.

    Artifact read I/O failure는 ``ArtifactProjectionReadError``로 노출한다.
    """

    digest = sha256()
    for path in (manifest_path, run_results_path):
        try:
            artifact_bytes = path.read_bytes()
        except OSError as exc:
            raise ArtifactProjectionReadError(path) from exc
        # 길이를 먼저 넣어 서로 다른 pair가 같은 byte concatenation으로 겹치지 않게 한다.
        digest.update(len(artifact_bytes).to_bytes(8, byteorder="big"))
        digest.update(artifact_bytes)
    return f"sha256:{digest.hexdigest()}"


@contextmanager
def artifact_projection_lock(directory: Path, *, exclusive: bool) -> Iterator[None]:
    """Current artifact pair access를 shared/exclusive local lock으로 직렬화한다.

    ``exclusive=False``는 shared reader lock, ``True``는 exclusive writer lock이다.
    Body exception은 그대로 보존하고, body가 성공한 경우에만 release failure를
    ``ArtifactProjectionLockError``로 노출한다.
    """

    try:
        directory.mkdir(parents=True, exist_ok=True)
        lock_file = (directory / ".artifact-promotion.lock").open("w")
        mode = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
        fcntl.flock(lock_file, mode)
    except OSError as exc:
        msg = f"dbt artifact projection lock을 획득할 수 없습니다: {directory}"
        raise ArtifactProjectionLockError(msg) from exc
    # body의 원래 예외가 뒤따른 unlock/close 실패로 가려지지 않게 추적한다.
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
