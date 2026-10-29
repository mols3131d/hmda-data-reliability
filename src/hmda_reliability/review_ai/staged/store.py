"""단계별 텍스트 실행의 bounded create-only 로컬 기록."""

from __future__ import annotations

import re
from pathlib import Path

from hmda_reliability.review_ai.staged.contracts import StagedReviewOutput, StageId
from hmda_reliability.review_ai.staged.evidence import StagedReviewManifest, StageRecord
from hmda_reliability.review_ai.store import (
    InvocationEvidenceExistsError,
    InvocationEvidenceWriteError,
    InvocationResponseStore,
    write_review_json,
)

_SAFE_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


class StagedReviewStore:
    """원문 포함 collection과 원문 없는 manifest를 구별해 보존한다."""

    def __init__(self, artifact_root: Path) -> None:
        self.artifact_root = Path(artifact_root)

    def directory(self, workflow_id: str) -> Path:
        if _SAFE_RUN_ID.fullmatch(workflow_id) is None:
            raise ValueError("unsafe workflow identity")
        return self.artifact_root / "agentic-review" / "staged" / workflow_id

    def reserve(self, workflow_id: str) -> None:
        """동일 실행의 재사용을 provider 호출 전에 거부한다."""
        from hmda_reliability.review_ai.staged.contracts import STAGE_IDS

        directory = self.directory(workflow_id)
        response_store = InvocationResponseStore(self.artifact_root)
        for stage in STAGE_IDS:
            invocation_id = f"{workflow_id}-{stage}"
            path = response_store.path_for(invocation_id)
            try:
                path.lstat()
            except FileNotFoundError:
                continue
            except OSError:
                raise InvocationEvidenceWriteError(
                    "staged response identity could not be inspected"
                ) from None
            raise InvocationEvidenceExistsError(
                "staged response identity already exists"
            )
        try:
            directory.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            directory.mkdir(mode=0o700)
        except FileExistsError:
            raise InvocationEvidenceExistsError(
                "workflow identity already exists"
            ) from None
        except OSError:
            raise InvocationEvidenceWriteError(
                "workflow directory could not be reserved"
            ) from None

    def stage_path(self, workflow_id: str, stage_id: StageId) -> Path:
        return self.directory(workflow_id) / f"{stage_id}.json"

    def write_stage(self, workflow_id: str, record: StageRecord) -> Path:
        return write_review_json(
            self.stage_path(workflow_id, record.stage_id),
            record.model_dump(mode="json"),
            max_record_bytes=65_536,
        )

    def write_output(
        self, workflow_id: str, output: StagedReviewOutput, *, max_bytes: int
    ) -> Path:
        return write_review_json(
            self.directory(workflow_id) / "output.json",
            output.model_dump(mode="json"),
            max_record_bytes=max_bytes,
        )

    def write_manifest(self, manifest: StagedReviewManifest) -> Path:
        return write_review_json(
            self.directory(manifest.workflow_id) / "workflow.json",
            manifest.model_dump(mode="json"),
            max_record_bytes=2_097_152,
        )

    def load(self, workflow_id: str) -> StagedReviewManifest:
        return StagedReviewManifest.model_validate_json(
            (self.directory(workflow_id) / "workflow.json").read_text(encoding="utf-8")
        )
