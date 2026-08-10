"""dbt artifact projection identity와 local reader/writer lock."""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path


class ArtifactProjectionLockError(Exception):
    """Artifact projection lock I/O에 실패했다."""


def artifact_projection_id(manifest_path: Path, run_results_path: Path) -> str:
    """Artifact pair 경계를 보존하는 projection identity를 반환한다."""

    digest = sha256()
    for path in (manifest_path, run_results_path):
        artifact_bytes = path.read_bytes()
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
    try:
        yield
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()
