"""원격에 내보낼 허용 IO만 로컬 원문·manifest와 다시 대조한다."""

import hashlib
import json
from pathlib import Path
from typing import Any

from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.evaluation.identity import digest, review_output_digest
from hmda_reliability.review_ai.prompt import build_canonical_input
from hmda_reliability.review_ai.staged.contracts import STAGE_IDS, StagedReviewOutput
from hmda_reliability.review_ai.staged.evidence import (
    StagedReviewManifest,
    StagedReviewResult,
)
from hmda_reliability.review_ai.staged.store import StagedReviewStore


def _read(path: Path, expected: Path, limit: int) -> bytes:
    if path.is_symlink() or path.absolute() != expected.absolute():
        raise ValueError("artifact_path_mismatch")
    with path.open("rb") as stream:
        body = stream.read(limit + 1)
    if len(body) > limit:
        raise ValueError("artifact_too_large")
    return body


def verify_local_result(
    result: StagedReviewResult, source: AgenticReviewInput, root: Path
) -> dict[str, Any]:
    if not result.workflow_id or not result.workflow_path:
        raise ValueError("workflow_missing")
    directory = StagedReviewStore(root).directory(result.workflow_id)
    manifest = StagedReviewManifest.model_validate_json(
        _read(result.workflow_path, directory / "workflow.json", 2_097_152)
    )
    canonical = build_canonical_input(source)
    if (
        manifest.project_revision != source.project_revision
        or manifest.workflow_id != result.workflow_id
        or manifest.status != result.status
        or manifest.stages != result.stages
        or manifest.canonical_input != canonical
        or manifest.output_path != result.output_path
        or manifest.failure_code != result.failure_code
    ):
        raise ValueError("workflow_binding_mismatch")
    stages = []
    for index, record in enumerate(manifest.stages):
        if record.stage_id != STAGE_IDS[index] or record.record_path is None:
            raise ValueError("stage_binding_mismatch")
        saved = json.loads(
            _read(record.record_path, directory / f"{record.stage_id}.json", 65_536)
        )
        if saved != record.model_dump(mode="json"):
            raise ValueError("stage_record_mismatch")
        text = None
        if record.response_path is not None:
            raw = _read(
                record.response_path,
                root
                / "agentic-review"
                / "responses"
                / f"{result.workflow_id}-{record.stage_id}.txt",
                manifest.configuration.max_output_bytes,
            )
            if "sha256:" + hashlib.sha256(raw).hexdigest() != record.response_digest:
                raise ValueError("response_digest_mismatch")
            text = raw.decode("utf-8")
        stages.append(
            dict(
                stage_id=record.stage_id,
                status=record.status,
                text=text,
                prompt_digest=record.prompt_digest,
                response_digest=record.response_digest,
                latency_ms=record.latency_ms,
                attempt_count=record.attempt_count,
                usage=record.usage.model_dump(mode="json") if record.usage else None,
                failure_code=record.failure_code,
            )
        )
    output = None
    if result.output_path is not None:
        parsed = StagedReviewOutput.model_validate_json(
            _read(result.output_path, directory / "output.json", 20_000_000)
        )
        if review_output_digest(parsed) != manifest.output_digest or (
            result.output is not None and result.output != parsed
        ):
            raise ValueError("output_digest_mismatch")
        if [s.text for s in parsed.stages] != [s["text"] for s in stages]:
            raise ValueError("output_text_mismatch")
        output = parsed.model_dump(mode="json")
    if result.status == "completed" and output is None:
        raise ValueError("output_missing")
    return dict(
        canonical_input=canonical,
        canonical_input_digest=digest(canonical),
        stages=stages,
        output=output,
        output_digest=manifest.output_digest,
        status=result.status,
        workflow_id=result.workflow_id,
    )
