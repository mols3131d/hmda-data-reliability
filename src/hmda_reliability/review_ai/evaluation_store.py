"""Review AI utility comparison의 생성 전용 local JSON evidence store."""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
from pathlib import Path

from hmda_reliability.review_ai.evaluation import (
    UtilityComparisonEvidence,
    UtilityProofBundle,
)
from hmda_reliability.review_ai.prompt import canonical_json_bytes

_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class UtilityEvidenceStoreError(Exception):
    """Utility comparison evidence를 저장할 수 없을 때 발생한다."""


class UtilityEvidenceExistsError(UtilityEvidenceStoreError):
    """Comparison identity가 이미 존재한다."""


class UtilityEvidenceStore:
    """Invocation evidence와 분리된 create-only comparison evidence store."""

    def __init__(self, artifact_root: Path) -> None:
        self._artifact_root = Path(artifact_root)

    def path_for(self, comparison_id: str) -> Path:
        if _SAFE_ID.fullmatch(comparison_id) is None:
            msg = "unsafe comparison identity"
            raise ValueError(msg)
        return (
            self._artifact_root / "agentic-review" / "utility" / f"{comparison_id}.json"
        )

    def write(self, evidence: UtilityComparisonEvidence) -> Path:
        return self._write(
            self.path_for(evidence.comparison_id),
            evidence.model_dump(mode="json"),
        )

    def write_proof(self, bundle: UtilityProofBundle) -> Path:
        path = self.path_for_proof(bundle.proof_id)
        return self._write(path, bundle.model_dump(mode="json"))

    def _write(self, path: Path, value: object) -> Path:
        payload = canonical_json_bytes(value) + b"\n"
        descriptor = -1
        temporary_path: Path | None = None
        linked = False
        try:
            path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            descriptor, raw_temporary_path = tempfile.mkstemp(
                prefix=f".{path.stem}.",
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
                raise UtilityEvidenceExistsError(
                    "utility comparison identity already exists"
                ) from error
            linked = True
            _fsync_directory(path.parent)
        except UtilityEvidenceExistsError:
            raise
        except OSError as error:
            if linked:
                try:
                    path.unlink(missing_ok=True)
                except OSError as rollback_error:
                    raise UtilityEvidenceStoreError(
                        "utility evidence write failed and rollback was indeterminate"
                    ) from rollback_error
            raise UtilityEvidenceStoreError("utility evidence write failed") from error
        finally:
            if descriptor >= 0:
                with contextlib.suppress(OSError):
                    os.close(descriptor)
            if temporary_path is not None:
                with contextlib.suppress(OSError):
                    temporary_path.unlink(missing_ok=True)
        return path

    def load(self, comparison_id: str) -> UtilityComparisonEvidence:
        return UtilityComparisonEvidence.model_validate_json(
            self.path_for(comparison_id).read_text(encoding="utf-8")
        )

    def load_proof(self, proof_id: str) -> UtilityProofBundle:
        return UtilityProofBundle.model_validate_json(
            self.path_for_proof(proof_id).read_text(encoding="utf-8")
        )

    def path_for_proof(self, proof_id: str) -> Path:
        if _SAFE_ID.fullmatch(proof_id) is None:
            msg = "unsafe proof identity"
            raise ValueError(msg)
        return (
            self._artifact_root
            / "agentic-review"
            / "utility"
            / "proofs"
            / f"{proof_id}.json"
        )


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(directory, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
