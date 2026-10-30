"""가상 사례를 실제 provider로 실행하는 opt-in 통합 검증 진입점.

python -m hmda_reliability.review_ai.evaluation.live로 실행한다.
실행·저장 성공을 검사하며 사람의 답변 품질 평가는 별도로 수행한다.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from pydantic import AnyHttpUrl, ValidationError

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
from hmda_reliability.review_ai import review_null_spike
from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.review_ai.evaluation.progress import LiveProgressReporter
from hmda_reliability.review_ai.evidence import (
    SanitizedAgenticReviewConfiguration,
)
from hmda_reliability.review_ai.prompt import (
    build_canonical_input,
    canonical_json_bytes,
)
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.review_ai.staged.contracts import StagedReviewOutput
from hmda_reliability.review_ai.staged.evidence import StagedReviewResult
from hmda_reliability.review_ai.staged.progress import ProgressCallback
from hmda_reliability.review_ai.staged.settings import StagedExecutionSettings
from hmda_reliability.review_ai.staged.store import StagedReviewStore
from hmda_reliability.runtime_ai import RuntimeAISettings

_TRUE_VALUES = {"1", "true", "yes", "on"}
_REQUIRED_ENVIRONMENT = (
    "HMDA_AGENTIC_REVIEW_BASE_URL",
    "HMDA_AGENTIC_REVIEW_API_KEY",
    "HMDA_AGENTIC_REVIEW_MODEL",
)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[4]


class Reviewer(Protocol):
    def __call__(
        self,
        *,
        incident: Incident,
        evidence: Sequence[Evidence],
        draft: RemediationDraft,
        project_revision: str,
        settings: RuntimeAISettings,
        review_settings: ReviewAISettings,
        execution_settings: StagedExecutionSettings,
        artifact_root: Path,
        on_progress: ProgressCallback | None = None,
    ) -> StagedReviewResult: ...


@dataclass(frozen=True)
class LiveReviewConfiguration:
    project_revision: str
    settings: RuntimeAISettings
    review_settings: ReviewAISettings
    execution_settings: StagedExecutionSettings
    artifact_root: Path


def load_live_configuration(environment: Mapping[str, str]) -> LiveReviewConfiguration:
    """단일 실행과 native 실험이 같은 provider·예산 설정을 사용한다."""
    project_revision = _project_revision(environment)
    connect_timeout = _optional_float_value(
        environment, "HMDA_AGENTIC_REVIEW_CONNECT_TIMEOUT_SECONDS"
    )
    read_timeout = _optional_float_value(
        environment, "HMDA_AGENTIC_REVIEW_READ_TIMEOUT_SECONDS"
    )
    if connect_timeout is None:
        connect_timeout = 10.0
    if read_timeout is None:
        read_timeout = _float_value(
            environment, "HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS", 300.0
        )
    settings = RuntimeAISettings(
        base_url=environment["HMDA_AGENTIC_REVIEW_BASE_URL"],
        api_key=environment["HMDA_AGENTIC_REVIEW_API_KEY"],
        model=environment["HMDA_AGENTIC_REVIEW_MODEL"],
        timeout_seconds=_float_value(
            environment,
            "HMDA_AGENTIC_REVIEW_TIMEOUT_SECONDS",
            30.0,
        ),
        connect_timeout_seconds=connect_timeout,
        read_timeout_seconds=read_timeout,
        max_retries=_int_value(
            environment,
            "HMDA_AGENTIC_REVIEW_MAX_RETRIES",
            0,
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
    execution_settings = StagedExecutionSettings(
        stage_budget_seconds=_float_value(
            environment, "HMDA_AGENTIC_REVIEW_STAGE_BUDGET_SECONDS", 360.0
        ),
        workflow_budget_seconds=_float_value(
            environment, "HMDA_AGENTIC_REVIEW_WORKFLOW_BUDGET_SECONDS", 1200.0
        ),
    )
    return LiveReviewConfiguration(
        project_revision,
        settings,
        review_settings,
        execution_settings,
        Path(environment.get("HMDA_RELIABILITY_ARTIFACTS_DIR", ".local/artifacts")),
    )


def main(
    *,
    env: Mapping[str, str] | None = None,
    reviewer: Reviewer = review_null_spike,
) -> int:
    """환경에서 명시적으로 켜면 Review AI 검증을 실행하고 결과를 출력한다.

    원문을 제외한 현재 단계별 실행의 상태와 경로만 표준 출력에 쓴다.
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
        config = load_live_configuration(environment)
    except (KeyError, ValueError, ValidationError):
        print("Invalid live agentic review configuration.", file=sys.stderr)
        return 2
    incident, evidence, draft = _build_null_spike_material()
    return _run_staged_live(
        reviewer=reviewer,
        incident=incident,
        evidence=evidence,
        draft=draft,
        project_revision=config.project_revision,
        settings=config.settings,
        review_settings=config.review_settings,
        execution_settings=config.execution_settings,
        artifact_root=config.artifact_root,
    )


def _run_staged_live(
    *,
    reviewer: Reviewer,
    incident: Incident,
    evidence: Evidence,
    draft: RemediationDraft,
    project_revision: str,
    settings: RuntimeAISettings,
    review_settings: ReviewAISettings,
    execution_settings: StagedExecutionSettings,
    artifact_root: Path,
) -> int:
    """모델 원문을 로컬 파일에 두고 수집 상태와 출처만 출력한다."""
    print(
        "가상 사례로 실제 모델 통합 검증 시작 (staged-v1)", file=sys.stderr, flush=True
    )
    with LiveProgressReporter() as progress:
        result = reviewer(
            incident=incident,
            evidence=[evidence],
            draft=draft,
            project_revision=project_revision,
            settings=settings,
            review_settings=review_settings,
            execution_settings=execution_settings,
            artifact_root=artifact_root,
            on_progress=progress,
        )
    print("최종 실행 기록과 출력 출처 검증", file=sys.stderr, flush=True)
    print(result.model_dump_json(indent=2, exclude={"output"}))
    if not _verify_staged_live_provenance(
        result,
        artifact_root=artifact_root,
        settings=settings,
        review_settings=review_settings,
        execution_settings=execution_settings,
        project_revision=project_revision,
        incident=incident,
        evidence=evidence,
        draft=draft,
    ):
        print("Live workflow provenance validation failed.", file=sys.stderr)
        return 1
    print(f"통합 검증 종료 · status={result.status}", file=sys.stderr, flush=True)
    return 0 if result.status == "completed" else 1


def _verify_staged_live_provenance(
    result: StagedReviewResult,
    *,
    artifact_root: Path,
    settings: RuntimeAISettings,
    review_settings: ReviewAISettings,
    execution_settings: StagedExecutionSettings,
    project_revision: str,
    incident: Incident,
    evidence: Evidence,
    draft: RemediationDraft,
) -> bool:
    """동일 사례의 manifest와 출력 내용을 재로드해 반환 결과와 대조한다."""
    if result.workflow_path is None:
        return result.status in {"input_rejected", "provenance_failed"}
    if result.workflow_id is None:
        return False
    store = StagedReviewStore(artifact_root)
    try:
        expected_directory = store.directory(result.workflow_id)
        if result.workflow_path != expected_directory / "workflow.json":
            return False
        record = store.load(result.workflow_id)
        expected_input = build_canonical_input(
            AgenticReviewInput(
                incident=incident,
                evidence=[evidence],
                draft=draft,
                project_revision=project_revision,
            )
        )
        if (
            record.workflow_id != result.workflow_id
            or record.status != result.status
            or record.project_revision != project_revision
            or not _configuration_matches(
                record.configuration, settings=settings, review_settings=review_settings
            )
            or record.execution_settings != execution_settings
            or canonical_json_bytes(record.canonical_input)
            != canonical_json_bytes(expected_input)
            or record.stages != result.stages
            or record.output_path != result.output_path
            or record.failure_code != result.failure_code
        ):
            return False
        if result.status != "completed" and result.output is not None:
            return False
        if result.output_path is None:
            return result.status != "completed" and record.output_digest is None
        if result.status == "completed" and result.output is None:
            return False
        if result.output_path != expected_directory / "output.json":
            return False
        output = StagedReviewOutput.model_validate_json(
            result.output_path.read_text(encoding="utf-8")
        )
        output_digest = (
            "sha256:"
            + hashlib.sha256(
                canonical_json_bytes(output.model_dump(mode="json"))
            ).hexdigest()
        )
        return output_digest == record.output_digest and (
            result.output is None or output == result.output
        )
    except (OSError, ValidationError, ValueError):
        return False


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
    source_file = _REPOSITORY_ROOT / "src/hmda_reliability/review_ai/evaluation/live.py"
    if (
        source_file.resolve() != Path(__file__).resolve()
        or not (_REPOSITORY_ROOT / "pyproject.toml").is_file()
        or not (_REPOSITORY_ROOT / ".git").exists()
    ):
        raise ValueError("auto project revision requires the loaded source checkout")
    # Hook·다른 checkout의 GIT_DIR/INDEX 설정으로 출처가 바뀌지 않게 한다.
    git_environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    try:
        revision_result = subprocess.run(
            ["git", "-C", str(_REPOSITORY_ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            env=git_environment,
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
            env=git_environment,
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


def _configuration_matches(
    recorded: SanitizedAgenticReviewConfiguration,
    *,
    settings: RuntimeAISettings,
    review_settings: ReviewAISettings,
) -> bool:
    expected = SanitizedAgenticReviewConfiguration.model_validate(
        {
            **settings.sanitized_configuration(),
            **review_settings.sanitized_configuration(),
        }
    )
    recorded_values = recorded.model_dump(exclude_none=True)
    expected_values = expected.model_dump(exclude_none=True)
    try:
        recorded_values["base_url"] = str(AnyHttpUrl(recorded.base_url))
        expected_values["base_url"] = str(AnyHttpUrl(expected.base_url))
    except ValueError:
        return False
    return recorded_values == expected_values


def _float_value(
    environment: Mapping[str, str],
    name: str,
    default: float,
) -> float:
    raw_value = environment.get(name)
    return default if raw_value is None or not raw_value.strip() else float(raw_value)


def _optional_float_value(environment: Mapping[str, str], name: str) -> float | None:
    raw_value = environment.get(name)
    return None if raw_value is None or not raw_value.strip() else float(raw_value)


def _int_value(
    environment: Mapping[str, str],
    name: str,
    default: int,
) -> int:
    raw_value = environment.get(name)
    return default if raw_value is None or not raw_value.strip() else int(raw_value)


if __name__ == "__main__":
    raise SystemExit(main())
