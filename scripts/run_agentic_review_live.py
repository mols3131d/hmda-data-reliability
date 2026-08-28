"""Opt-in Ollama-compatible bounded agentic review proof."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from pydantic import ValidationError

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
    AgenticReviewResult,
    PromptIdentity,
    review_null_spike,
)
from hmda_reliability.review_ai.contracts import (
    AgenticReviewStatus,
    ReviewValidationStatus,
)
from hmda_reliability.review_ai.evidence import AgenticInvocationEvidence
from hmda_reliability.review_ai.prompt import render_canonical_input
from hmda_reliability.review_ai.settings import ReviewAISettings
from hmda_reliability.runtime_ai import RuntimeAISettings

_TRUE_VALUES = {"1", "true", "yes", "on"}
_REQUIRED_ENVIRONMENT = (
    "HMDA_AGENTIC_REVIEW_BASE_URL",
    "HMDA_AGENTIC_REVIEW_API_KEY",
    "HMDA_AGENTIC_REVIEW_MODEL",
)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


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
    """Run one real provider proof only after explicit environment opt-in."""

    environment = os.environ if env is None else env
    enabled = environment.get("HMDA_AGENTIC_REVIEW_LIVE", "").strip().lower()
    if enabled not in _TRUE_VALUES:
        print("Agentic review live proof is disabled.")
        return 0

    missing = [
        name for name in _REQUIRED_ENVIRONMENT if not environment.get(name, "").strip()
    ]
    if missing:
        print(
            "Missing live configuration: " + ", ".join(missing),
            file=sys.stderr,
        )
        return 2

    try:
        project_revision = _project_revision(environment)
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
    except (KeyError, ValueError, ValidationError):
        print("Invalid live agentic review configuration.", file=sys.stderr)
        return 2

    incident, evidence, draft = _build_null_spike_material()
    result = reviewer(
        incident=incident,
        evidence=[evidence],
        draft=draft,
        prompt_identity=PromptIdentity(),
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
    return 0 if result.status == "accepted" else 1


def _project_revision(environment: Mapping[str, str]) -> str:
    configured = environment.get("HMDA_AGENTIC_REVIEW_PROJECT_REVISION", "").strip()
    if configured and configured.lower() != "auto":
        return configured
    return _current_git_revision()


def _current_git_revision() -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(_REPOSITORY_ROOT), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError("project revision could not be resolved from Git") from error

    revision = completed.stdout.strip()
    if not revision:
        raise ValueError("project revision could not be resolved from Git")
    return revision


def _build_null_spike_material() -> tuple[Incident, Evidence, RemediationDraft]:
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
) -> bool:
    if result.status in {
        AgenticReviewStatus.INPUT_REJECTED,
        AgenticReviewStatus.PROVENANCE_FAILED,
    }:
        return True
    if result.invocation_id is None or result.invocation_path is None:
        return False

    try:
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
