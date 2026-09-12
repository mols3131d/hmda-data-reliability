"""dbt artifact pair identity와 current projection의 local lock primitive."""

from __future__ import annotations

import fcntl
from collections.abc import Iterator
from contextlib import contextmanager
from hashlib import sha256
from pathlib import Path


class ArtifactProjectionLockError(Exception):
    """Projection lock 준비·해제 과정의 I/O 실패를 나타낸다."""


class ArtifactProjectionReadError(Exception):
    """Projection identity 계산 중 artifact read 실패를 나타낸다."""

    def __init__(self, artifact_path: Path) -> None:
        super().__init__(f"dbt artifact를 읽을 수 없습니다: {artifact_path}")
        self.artifact_path = artifact_path


def artifact_projection_id(manifest_path: Path, run_results_path: Path) -> str:
    """Artifact 순서와 byte 경계를 보존한 projection identity를 계산한다.

    Identity 구조:
        - 두 아티팩트(`manifest_path`, `run_results_path`)의 길이를
          각각 8바이트 big-endian 정수로 해시 다이제스트에 주입 후 바이트를 추가한다.
        - 이는 길이가 다른 두 아티팩트 바이트 배열의 단순 결합 시 생길 수 있는
          바운더리 충돌(e.g., A + B == A' + B')을 암호학적으로 방지한다.

    Exceptions:
        - ArtifactProjectionReadError: 아티팩트 파일 읽기 I/O 실패 시 발생.
    """

    digest = sha256()
    for path in (manifest_path, run_results_path):
        try:
            artifact_bytes = path.read_bytes()
        except OSError as exc:
            raise ArtifactProjectionReadError(path) from exc
        # 각 artifact 길이를 먼저 넣어 다른 pair가 같은 byte 연결로 겹치지 않게 한다.
        digest.update(len(artifact_bytes).to_bytes(8, byteorder="big"))
        digest.update(artifact_bytes)
    return f"sha256:{digest.hexdigest()}"


@contextmanager
def artifact_projection_lock(directory: Path, *, exclusive: bool) -> Iterator[None]:
    """Current artifact pair 접근을 shared/exclusive local lock으로 직렬화한다.

    Lock 규칙 및 예외 보존 정책:
        - `exclusive=False`: shared reader lock (`fcntl.LOCK_SH`).
          복수 프로세스의 동시 읽기 허용.
        - `exclusive=True`: exclusive writer lock (`fcntl.LOCK_EX`).
          단일 프로세스의 승격(promotion) 전용.
        - Body 블록 실행 중 예외는 뒤따른 unlock/close 실패보다 우선 보존된다.
        - Body가 성공한 경우에만 unlock 실패가 `ArtifactProjectionLockError`로 노출된다.
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
