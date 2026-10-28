"""명시적으로 켜면 Ollama 호환 제공자로 검토를 실행하는 CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

from hmda_reliability.logger import get_logger
from hmda_reliability.reliability import (
    DetectionRequest,
    Evidence,
    FreshnessMeasurementStatus,
    Incident,
    ProfileSnapshot,
    RemediationDraft,
    RemediationDraftRequest,
    create_remediation_draft,
    detect_basic_incidents,
)
from hmda_reliability.review_ai import (
    AgenticReviewInput,
    AgenticReviewResult,
    PromptIdentity,
    review_null_spike,
)
from hmda_reliability.review_ai.contracts import (
    AgenticReviewStatus,
    ReviewValidationStatus,
)
from hmda_reliability.review_ai.evidence import AgenticInvocationEvidence
from hmda_reliability.review_ai.prompt import (
    build_canonical_input,
    render_canonical_input,
)
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.runtime_ai import RuntimeAISettings

_TRUE_VALUES = {"1", "true", "yes", "on"}
_REQUIRED_ENVIRONMENT = (
    "HMDA_AGENTIC_REVIEW_BASE_URL",
    "HMDA_AGENTIC_REVIEW_API_KEY",
    "HMDA_AGENTIC_REVIEW_MODEL",
)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
_LOGGER = get_logger(__name__)


class Reviewer(Protocol):
    def __call__(
        self,
        *,
        incident: Incident,
        evidence: Sequence[Evidence],
        draft: RemediationDraft,
        prompt_identity: PromptIdentity,
        project_revision: str,
        settings: RuntimeAISettings,
        review_settings: ReviewAISettings,
        artifact_root: Path,
    ) -> AgenticReviewResult: ...


def main(
    *,
    env: Mapping[str, str] | None = None,
    reviewer: Reviewer = review_null_spike,
) -> int:
    """환경에서 명시적으로 켜면 Review AI 검증을 실행하고 결과를 출력한다.

    검토 결과 JSON은 표준 출력에, 선택적 Langfuse 투영 상태는 표준 오류에 쓴다.
    투영 실패는 이미 확정된 검토 결과와 CLI 종료 코드를 바꾸지 않는다.
    """

    environment = os.environ if env is None else env
    enabled = environment.get("HMDA_AGENTIC_REVIEW_LIVE", "").strip().lower()
    if enabled not in _TRUE_VALUES:
        print("Agentic review live proof is disabled.")
        return 0

    missing_env_vars = [
        name for name in _REQUIRED_ENVIRONMENT if not environment.get(name, "").strip()
    ]
    if missing_env_vars:
        print(
            "Missing live configuration: " + ", ".join(missing_env_vars),
            file=sys.stderr,
        )
        return 2

    try:
        project_revision = _project_revision(environment)
    except ValueError as error:
        print(
            f"Invalid live agentic review configuration: project revision: {error}",
            file=sys.stderr,
        )
        return 2

    try:
        settings = RuntimeAISettings(
            base_url=environment["HMDA_AGENTIC_REVIEW_BASE_URL"],
            api_key=environment["HMDA_AGENTIC_REVIEW_API_KEY"],
            model=environment["HMDA_AGENTIC_REVIEW_MODEL"],
            timeout_seconds=_float_value(
                environment,
                "HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS",
                30.0,
            ),
            max_retries=_int_value(
                environment,
                "HMDA_AGENTIC_REVIEW_MAX_RETRIES",
                1,
            ),
            max_output_tokens=_int_value(
                environment,
                "HMDA_AGENTIC_REVIEW_MAX_OUTPUT_TOKENS",
                1024,
            ),
            max_output_bytes=_int_value(
                environment,
                "HMDA_AGENTIC_REVIEW_MAX_OUTPUT_BYTES",
                32_768,
            ),
        )
        review_settings = ReviewAISettings(
            max_prompt_bytes=_int_value(
                environment,
                "HMDA_AGENTIC_REVIEW_MAX_PROMPT_BYTES",
                65_536,
            )
        )
        prompt_identity = PromptIdentity.model_validate(
            {
                "version": environment.get("HMDA_AGENTIC_REVIEW_PROMPT_VERSION", "v2"),
            }
        )
    except (KeyError, ValueError, ValidationError):
        print("Invalid live agentic review configuration.", file=sys.stderr)
        return 2

    incident, evidence, draft = _build_null_spike_material()
    result = reviewer(
        incident=incident,
        evidence=[evidence],
        draft=draft,
        prompt_identity=prompt_identity,
        project_revision=project_revision,
        settings=settings,
        review_settings=review_settings,
        artifact_root=Path(
            environment.get(
                "HMDA_RELIABILITY_ARTIFACTS_DIR",
                ".local/artifacts",
            )
        ),
    )
    print(result.model_dump_json(indent=2))
    if not _verify_live_provenance(
        result,
        settings=settings,
        review_settings=review_settings,
        project_revision=project_revision,
    ):
        print("Live invocation provenance validation failed.", file=sys.stderr)
        return 3
    if environment.get("HMDA_LANGFUSE_EXPORT", "").strip().lower() in _TRUE_VALUES:
        integration_status = _export_live_projection(
            result,
            environment=environment,
            settings=settings,
            review_settings=review_settings,
            project_revision=project_revision,
            incident=incident,
            evidence=evidence,
            draft=draft,
        )
        print(f"Langfuse projection: {integration_status}", file=sys.stderr)
    return 0 if result.status == "accepted" else 1


def _export_live_projection(
    result: AgenticReviewResult,
    *,
    environment: Mapping[str, str],
    settings: RuntimeAISettings,
    review_settings: ReviewAISettings,
    project_revision: str,
    incident: Incident,
    evidence: Evidence,
    draft: RemediationDraft,
) -> str:
    """검증된 호출 기록만 선택적 Langfuse 전송 자료로 변환한다.

    입력 거부나 기록 누락은 `skipped_no_record`, 기록 검증 실패는
    `skipped_invalid_record`를 반환한다. 예상 밖 오류는 `projection_failed`로
    줄여 반환하고 이미 나온 검토 결과는 유지한다.
    """
    if result.status in {
        AgenticReviewStatus.INPUT_REJECTED,
        AgenticReviewStatus.PROVENANCE_FAILED,
    }:
        return "skipped_no_record"
    # 선택적 투영이 실패해도 이미 검증된 검토 결과를 보존한다.
    try:
        from hmda_reliability.review_ai.evaluation.langfuse import (
            export_projection,
            project_invocation,
        )

        if result.invocation_path is None:
            return "skipped_no_record"
        record = AgenticInvocationEvidence.model_validate_json(
            result.invocation_path.read_text(encoding="utf-8")
        )
        if not _verify_live_provenance(
            result,
            settings=settings,
            review_settings=review_settings,
            project_revision=project_revision,
            record=record,
        ):
            return "skipped_invalid_record"
        expected_input = build_canonical_input(
            AgenticReviewInput(
                incident=incident,
                evidence=[evidence],
                draft=draft,
                prompt_identity=PromptIdentity(),
                project_revision=project_revision,
            )
        )
        payload = project_invocation(record, expected_input=expected_input)
        return export_projection(payload, env=environment)
    except Exception as error:
        _LOGGER.debug("선택적 Langfuse 투영 처리 실패: %s", type(error).__name__)
        return "projection_failed"


def _project_revision(environment: Mapping[str, str]) -> str:
    """설정값을 반환하거나, `auto`이면 tracked 파일이 깨끗할 때 Git HEAD를 반환한다.

    자동 판정은 untracked 파일을 검사하지 않는다.
    """
    configured = environment.get("HMDA_AGENTIC_REVIEW_PROJECT_REVISION", "").strip()
    if configured and configured.lower() != "auto":
        return configured
    return _current_git_revision()


def _current_git_revision() -> str:
    """추적 중인 파일에 수정이 없을 때만 현재 Git HEAD를 출처용 리비전으로 쓴다."""
    try:
        revision_result = subprocess.run(
            ["git", "-C", str(_REPOSITORY_ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        status_result = subprocess.run(
            [
                "git",
                "-C",
                str(_REPOSITORY_ROOT),
                "status",
                "--porcelain",
                "--untracked-files=no",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError("project revision could not be resolved from Git") from error

    revision = revision_result.stdout.strip()
    if not revision:
        raise ValueError("project revision could not be resolved from Git")
    if status_result.stdout.strip():
        raise ValueError("auto project revision requires a clean tracked worktree")
    return revision


def _build_null_spike_material() -> tuple[Incident, Evidence, RemediationDraft]:
    """외부 HMDA 자료를 읽지 않고 검증용 합성 `null_spike` 사례를 만든다."""
    observed_at = datetime(2026, 8, 27, 0, 0, tzinfo=UTC)
    baseline = ProfileSnapshot(
        snapshot_id="agentic-live-baseline-2025",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=observed_at,
        row_count=100,
        null_rates={"income": 0.01},
        schema_hash="sha256:agentic-live-proof",
        freshness_at=None,
        freshness_status=FreshnessMeasurementStatus.UNAVAILABLE,
    )
    current = ProfileSnapshot(
        snapshot_id="agentic-live-current-2025",
        asset_name="raw.hmda_loans",
        partition="2025",
        observed_at=observed_at,
        row_count=100,
        null_rates={"income": 0.21},
        schema_hash="sha256:agentic-live-proof",
        freshness_at=None,
        freshness_status=FreshnessMeasurementStatus.UNAVAILABLE,
    )
    detections = detect_basic_incidents(
        DetectionRequest(baseline=baseline, current=current)
    )
    if len(detections) != 1 or detections[0].incident.incident_type != "null_spike":
        msg = "live proof fixture did not produce exactly one null_spike incident"
        raise RuntimeError(msg)
    detection = detections[0]
    draft = create_remediation_draft(
        RemediationDraftRequest(
            incident=detection.incident,
            evidence=detection.evidence,
        )
    )
    return detection.incident, detection.evidence, draft


def _verify_live_provenance(
    result: AgenticReviewResult,
    *,
    settings: RuntimeAISettings,
    review_settings: ReviewAISettings,
    project_revision: str,
    record: AgenticInvocationEvidence | None = None,
) -> bool:
    """검토 결과와 호출 기록의 식별 정보 및 출처를 대조한다.

    호출 ID, 상태, 모델, prompt 크기 설정, 프로젝트 리비전, prompt 해시를
    확인한다. `ACCEPTED`이면 `parsed_output`과 `validation`을, 그 외 상태면
    `failure_code`를 추가로 대조한다. `record`가 없으면 결과 경로에서 읽는다.
    `INPUT_REJECTED`와 `PROVENANCE_FAILED`는 기록 없이도 유효한 결과로 처리한다.
    """
    if result.status in {
        AgenticReviewStatus.INPUT_REJECTED,
        AgenticReviewStatus.PROVENANCE_FAILED,
    }:
        return True
    if result.invocation_id is None or result.invocation_path is None:
        return False

    try:
        if record is None:
            record = AgenticInvocationEvidence.model_validate_json(
                result.invocation_path.read_text(encoding="utf-8")
            )
        replay = render_canonical_input(
            record.canonical_input,
            record.prompt_identity,
            max_prompt_bytes=review_settings.max_prompt_bytes,
        )
    except (OSError, ValidationError, ValueError):
        return False

    common_matches = (
        record.invocation_id == result.invocation_id
        and record.status is result.status
        and record.configuration.model == settings.model
        and record.configuration.max_prompt_bytes == review_settings.max_prompt_bytes
        and record.project_revision == project_revision.strip()
        and replay.prompt_digest == record.prompt_digest
    )
    if not common_matches:
        return False
    if result.status is AgenticReviewStatus.ACCEPTED:
        return (
            record.parsed_output == result.output
            and record.validation == result.validation
            and record.validation is not None
            and record.validation.status is ReviewValidationStatus.ACCEPTED
        )
    return record.failure_code == result.failure_code


def _float_value(
    environment: Mapping[str, str],
    name: str,
    default: float,
) -> float:
    raw_value = environment.get(name)
    return default if raw_value is None or not raw_value.strip() else float(raw_value)


def _int_value(
    environment: Mapping[str, str],
    name: str,
    default: int,
) -> int:
    raw_value = environment.get(name)
    return default if raw_value is None or not raw_value.strip() else int(raw_value)


if __name__ == "__main__":
    raise SystemExit(main())
