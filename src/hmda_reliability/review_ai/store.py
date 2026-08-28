"""Create-only local JSON invocation evidence store."""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
from pathlib import Path

from hmda_reliability.review_ai.evidence import AgenticInvocationEvidence
from hmda_reliability.review_ai.prompt import canonical_json_bytes

_SAFE_INVOCATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class InvocationEvidenceStoreError(Exception):
    """Invocation evidence could not be persisted safely."""


class InvocationEvidenceExistsError(InvocationEvidenceStoreError):
    """The immutable invocation identity already exists."""


class InvocationEvidenceSizeError(InvocationEvidenceStoreError):
    """The sanitized record exceeds the configured storage boundary."""


class InvocationEvidenceWriteError(InvocationEvidenceStoreError):
    """The sanitized record could not be durably created."""


class InvocationEvidenceStore:
    """Persist bounded records under an explicit local artifact root."""

    def __init__(self, artifact_root: Path) -> None:
        self._artifact_root = Path(artifact_root)

    def path_for(self, invocation_id: str) -> Path:
        if _SAFE_INVOCATION_ID.fullmatch(invocation_id) is None:
            msg = "unsafe invocation identity"
            raise ValueError(msg)
        return (
            self._artifact_root
            / "agentic-review"
            / "invocations"
            / f"{invocation_id}.json"
        )

    def write(
        self,
        record: AgenticInvocationEvidence,
        *,
        max_record_bytes: int,
    ) -> Path:
        payload = canonical_json_bytes(record.model_dump(mode="json")) + b"\n"
        if len(payload) > max_record_bytes:
            raise InvocationEvidenceSizeError(
                "invocation evidence exceeds max_record_bytes"
            )

        path = self.path_for(record.invocation_id)
        descriptor = -1
        temporary_path: Path | None = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            descriptor, raw_temporary_path = tempfile.mkstemp(
                prefix=f".{record.invocation_id}.",
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

    def load(self, invocation_id: str) -> AgenticInvocationEvidence:
        path = self.path_for(invocation_id)
        return AgenticInvocationEvidence.model_validate_json(
            path.read_text(encoding="utf-8")
        )


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
