"""생성 전용 로컬 호출 evidence 및 원문 응답 저장소 모듈."""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
from pathlib import Path

from hmda_reliability.review_ai.prompt import canonical_json_bytes

_SAFE_INVOCATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class InvocationEvidenceStoreError(Exception):
    """호출 evidence를 안전하게 영속화할 수 없을 때 발생하는 기본 예외."""


class InvocationEvidenceExistsError(InvocationEvidenceStoreError):
    """불변의 호출 식별자가 이미 존재할 때 발생하는 예외."""


class InvocationEvidenceSizeError(InvocationEvidenceStoreError):
    """정제된 레코드 크기가 설정된 저장소 한도를 초과할 때 발생하는 예외."""


class InvocationEvidenceWriteError(InvocationEvidenceStoreError):
    """정제된 레코드를 영속적으로 생성할 수 없을 때 발생하는 예외."""


class InvocationResponseStore:
    """검증 전 provider 응답을 invocation evidence와 분리해 로컬에 보존한다."""

    def __init__(self, artifact_root: Path) -> None:
        self._artifact_root = Path(artifact_root)

    def path_for(self, invocation_id: str) -> Path:
        _validate_invocation_id(invocation_id)
        return (
            self._artifact_root
            / "agentic-review"
            / "responses"
            / f"{invocation_id}.txt"
        )

    def write(
        self,
        invocation_id: str,
        content: str,
        *,
        max_response_bytes: int,
    ) -> Path:
        """UTF-8 원문을 변형 없이 저장하고 기존 invocation과의 충돌을 거부한다."""
        try:
            payload = content.encode("utf-8")
        except UnicodeEncodeError:
            raise InvocationEvidenceWriteError(
                "invocation response cannot be encoded as UTF-8"
            ) from None
        if len(payload) > max_response_bytes:
            raise InvocationEvidenceSizeError(
                "invocation response exceeds max_response_bytes"
            )

        return _write_create_only(
            self.path_for(invocation_id),
            payload,
            invocation_id=invocation_id,
        )


def _validate_invocation_id(invocation_id: str) -> None:
    if _SAFE_INVOCATION_ID.fullmatch(invocation_id) is None:
        msg = "unsafe invocation identity"
        raise ValueError(msg)


def write_review_json(
    path: Path,
    payload: dict[str, object],
    *,
    max_record_bytes: int,
) -> Path:
    """Review AI의 별도 JSON artifact를 bounded create-only 파일로 보존한다."""
    _validate_invocation_id(path.stem)
    encoded = canonical_json_bytes(payload) + b"\n"
    if len(encoded) > max_record_bytes:
        raise InvocationEvidenceSizeError("review artifact exceeds max_record_bytes")
    return _write_create_only(path, encoded, invocation_id=path.stem)


def _write_create_only(
    path: Path,
    payload: bytes,
    *,
    invocation_id: str,
) -> Path:
    descriptor = -1
    temporary_path: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        descriptor, raw_temporary_path = tempfile.mkstemp(
            prefix=f".{invocation_id}.",
            suffix=".tmp",
            dir=path.parent,
        )
        temporary_path = Path(raw_temporary_path)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary_path, path)
        except FileExistsError as error:
            raise InvocationEvidenceExistsError(
                "invocation evidence identity already exists"
            ) from error
        try:
            _fsync_directory(path.parent)
        except OSError:
            with contextlib.suppress(OSError):
                path.unlink(missing_ok=True)
            raise
    except InvocationEvidenceExistsError:
        raise
    except OSError as error:
        raise InvocationEvidenceWriteError(
            "invocation evidence create-only write failed"
        ) from error
    finally:
        if descriptor >= 0:
            with contextlib.suppress(OSError):
                os.close(descriptor)
        if temporary_path is not None:
            with contextlib.suppress(OSError):
                temporary_path.unlink(missing_ok=True)
    return path


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
