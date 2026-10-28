"""제한된(bounded) agentic review를 위한 구조화된 계약 모델 정의."""

from __future__ import annotations

import json
from copy import deepcopy
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

from hmda_reliability.reliability.contracts import Evidence, EvidenceSource, Incident
from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.reliability.remediation import RemediationDraft

_EvidenceReference = Annotated[str, Field(min_length=1, max_length=256)]
_BoundedReviewText = Annotated[str, Field(min_length=1, max_length=4096)]


class FindingKind(StrEnum):
    OBSERVATION = "observation"
    CONCERN = "concern"
    OMISSION = "omission"
    UNCERTAINTY = "uncertainty"


class AdvisoryRecommendation(StrEnum):
    SUPPORT = "support"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class UtilityContributionKind(StrEnum):
    EVIDENCE_GAP = "evidence_gap"
    INVESTIGATION_PRIORITY = "investigation_priority"
    REMEDIATION_CRITIQUE = "remediation_critique"
    MATERIAL_UNCERTAINTY = "material_uncertainty"


class UtilityPriority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewViolationCode(StrEnum):
    FABRICATED_EVIDENCE = "fabricated_evidence"
    INCIDENT_MISMATCH = "incident_mismatch"
    DETERMINISTIC_CONTRADICTION = "deterministic_contradiction"
    # Historical values remain readable in forbidden-action-policy-v1 evidence.
    AUTHORITY_ESCALATION = "authority_escalation"
    FORBIDDEN_ACTION = "forbidden_action"


class ReviewValidationStatus(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class AgenticReviewStatus(StrEnum):
    ACCEPTED = "accepted"
    VALIDATION_FAILED = "validation_failed"
    UNAVAILABLE = "unavailable"
    INPUT_REJECTED = "input_rejected"
    PROVENANCE_FAILED = "provenance_failed"


class PromptIdentity(ReliabilityContract):
    template_id: Literal["reliability-agentic-review.null-spike"] = (
        "reliability-agentic-review.null-spike"
    )
    version: Literal["v1", "v2", "v3"] = "v1"


class NullSpikeFacts(ReliabilityContract):
    baseline_null_rate: float = Field(ge=0, le=1)
    current_null_rate: float = Field(ge=0, le=1)
    delta: float = Field(ge=0, le=1)
    threshold: float = Field(ge=0, le=1)


class AgenticReviewInput(ReliabilityContract):
    """결정론적 review 실행을 위한 불변의 입력 스냅샷 계약.

    모든 중첩 모델(Incident, Evidence, RemediationDraft)을 깊은 복사
    스냅샷으로 격리하여 외부의 후속 변경으로부터 review 불변식을 보호한다.
    """

    incident: Incident
    evidence: tuple[Evidence, ...] = Field(min_length=1, max_length=64)
    draft: RemediationDraft
    prompt_identity: PromptIdentity
    project_revision: str = Field(min_length=1, max_length=256)

    @field_validator("incident", mode="before")
    @classmethod
    def _snapshot_incident(cls, value: object) -> object:
        return _snapshot_model(value, Incident)

    @field_validator("evidence", mode="before")
    @classmethod
    def _snapshot_evidence(cls, value: object) -> object:
        if not isinstance(value, (list, tuple)):
            return deepcopy(value)
        return tuple(_snapshot_model(item, Evidence) for item in value)

    @field_validator("draft", mode="before")
    @classmethod
    def _snapshot_draft(cls, value: object) -> object:
        return _snapshot_model(value, RemediationDraft)

    @field_validator("project_revision")
    @classmethod
    def _normalize_revision(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            msg = "project_revision must be non-empty"
            raise ValueError(msg)
        return normalized

    @model_validator(mode="after")
    def _validate_review_input(self) -> AgenticReviewInput:
        if (
            self.incident.incident_type != "null_spike"
            or self.draft.incident_type != "null_spike"
        ):
            msg = "agentic review supports only null_spike incidents"
            raise ValueError(msg)

        incident_identity = (
            self.incident.incident_id,
            self.incident.asset_name,
            self.incident.partition,
        )
        draft_identity = (
            self.draft.incident_id,
            self.draft.asset_name,
            self.draft.partition,
        )
        if incident_identity != draft_identity:
            msg = "incident and draft identity must match"
            raise ValueError(msg)

        evidence_ids = [item.evidence_id for item in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            msg = "evidence IDs must be unique"
            raise ValueError(msg)
        expected_ids = set(self.incident.evidence_refs)
        if (
            set(evidence_ids) != expected_ids
            or set(self.draft.evidence_refs) != expected_ids
        ):
            msg = "provided evidence must match incident and draft references"
            raise ValueError(msg)

        target = _canonical_target(
            self.evidence,
            asset_name=self.incident.asset_name,
            partition=self.incident.partition,
        )
        for item in self.evidence:
            _validate_canonical_json(item.payload)

        _target_column(target)
        _null_spike_facts(target)
        return self

    @property
    def target_column(self) -> str:
        return _target_column(
            _canonical_target(
                self.evidence,
                asset_name=self.incident.asset_name,
                partition=self.incident.partition,
            )
        )

    @property
    def deterministic_facts(self) -> NullSpikeFacts:
        return _null_spike_facts(
            _canonical_target(
                self.evidence,
                asset_name=self.incident.asset_name,
                partition=self.incident.partition,
            )
        )


class AgenticReviewFinding(ReliabilityContract):
    kind: FindingKind
    description: str = Field(min_length=1, max_length=4096)
    evidence_refs: tuple[_EvidenceReference, ...] = Field(default=(), max_length=64)

    @field_validator("description")
    @classmethod
    def _normalize_description(cls, value: str) -> str:
        return _non_empty(value, field_name="description")

    @field_validator("evidence_refs")
    @classmethod
    def _normalize_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _normalized_unique_strings(values, field_name="evidence_refs")


class AgenticReviewUtilityContribution(ReliabilityContract):
    kind: UtilityContributionKind
    description: str = Field(min_length=1, max_length=4096)
    evidence_refs: tuple[_EvidenceReference, ...] = Field(default=(), max_length=64)
    priority: UtilityPriority | None = None

    @field_validator("description")
    @classmethod
    def _normalize_description(cls, value: str) -> str:
        return _non_empty(value, field_name="utility contribution description")

    @field_validator("evidence_refs")
    @classmethod
    def _normalize_evidence_refs(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _normalized_unique_strings(values, field_name="utility evidence_refs")

    @model_validator(mode="after")
    def _validate_priority(self) -> AgenticReviewUtilityContribution:
        if (
            self.kind is UtilityContributionKind.INVESTIGATION_PRIORITY
            and self.priority is None
        ):
            msg = "investigation_priority requires a priority"
            raise ValueError(msg)
        if (
            self.kind is not UtilityContributionKind.INVESTIGATION_PRIORITY
            and self.priority is not None
        ):
            msg = "priority is only valid for investigation_priority"
            raise ValueError(msg)
        return self


class AgenticReviewOutput(ReliabilityContract):
    incident_id: str = Field(min_length=1, max_length=256)
    incident_type: Literal["null_spike"]
    target_column: str = Field(min_length=1, max_length=256)
    deterministic_facts: NullSpikeFacts
    review_summary: str = Field(min_length=1, max_length=4096)
    evidence_used: tuple[_EvidenceReference, ...] = Field(min_length=1, max_length=64)
    findings: tuple[AgenticReviewFinding, ...] = Field(max_length=64)
    uncertainties: tuple[_BoundedReviewText, ...] = Field(max_length=64)
    advisory_recommendation: AdvisoryRecommendation
    utility_contributions: tuple[AgenticReviewUtilityContribution, ...] = Field(
        default=(),
        max_length=64,
    )

    @field_validator("incident_id", "target_column", "review_summary")
    @classmethod
    def _normalize_text(cls, value: str, info: ValidationInfo) -> str:
        return _non_empty(value, field_name=info.field_name or "text")

    @field_validator("evidence_used")
    @classmethod
    def _normalize_evidence_used(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return _normalized_unique_strings(values, field_name="evidence_used")

    @field_validator("uncertainties")
    @classmethod
    def _normalize_uncertainties(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(_non_empty(value, field_name="uncertainties") for value in values)


class AgenticReviewValidation(ReliabilityContract):
    """출처 증명에 보존되는 버전 관리된 결정론적 검증 결과 모델."""

    status: ReviewValidationStatus
    violations: tuple[ReviewViolationCode, ...]
    policy_id: Literal[
        "structured-fact-validation-v1",
        "forbidden-action-policy-v1",
    ] = "structured-fact-validation-v1"

    @model_validator(mode="after")
    def _validate_status(self) -> AgenticReviewValidation:
        if len(self.violations) != len(set(self.violations)):
            msg = "validation violations must be unique"
            raise ValueError(msg)
        if self.status is ReviewValidationStatus.ACCEPTED and self.violations:
            msg = "accepted validation cannot contain violations"
            raise ValueError(msg)
        if self.status is ReviewValidationStatus.REJECTED and not self.violations:
            msg = "rejected validation requires at least one violation"
            raise ValueError(msg)
        if self.policy_id == "structured-fact-validation-v1" and any(
            violation
            in {
                ReviewViolationCode.AUTHORITY_ESCALATION,
                ReviewViolationCode.FORBIDDEN_ACTION,
            }
            for violation in self.violations
        ):
            msg = "structured fact validation forbids legacy text-policy violations"
            raise ValueError(msg)
        return self


class AgenticReviewResult(ReliabilityContract):
    """Review 오케스트레이션 결과 및 출처 증명 경계를 캡슐화한 불변 결과 모델.

    상태별 불변식:
    - `ACCEPTED`: output, validation, invocation_id/path 필수. failure_code는 None.
    - `VALIDATION_FAILED` / `UNAVAILABLE`: durable invocation_id/path 필수.
      output 노출 금지, failure_code 필수.
    - `INPUT_REJECTED`: provider 호출 전 거부이므로 invocation 출처 메타데이터 금지.
    - `PROVENANCE_FAILED`: invocation_id는 존재하나 디스크 쓰기 실패로
      invocation_path는 None.
    """

    status: AgenticReviewStatus
    output: AgenticReviewOutput | None = None
    validation: AgenticReviewValidation | None = None
    invocation_id: str | None = None
    invocation_path: Path | None = None
    failure_code: str | None = None

    @field_validator("invocation_id", "failure_code")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _non_empty(value, field_name="result field")

    @model_validator(mode="after")
    def _validate_result_boundary(self) -> AgenticReviewResult:
        if self.status is AgenticReviewStatus.ACCEPTED:
            if (
                self.output is None
                or self.validation is None
                or self.validation.status is not ReviewValidationStatus.ACCEPTED
                or self.invocation_id is None
                or self.invocation_path is None
                or self.failure_code is not None
            ):
                msg = "accepted result requires output, validation, and provenance"
                raise ValueError(msg)
            return self

        if self.output is not None:
            msg = "non-accepted result cannot expose provider output"
            raise ValueError(msg)
        if self.failure_code is None:
            msg = "non-accepted result requires a failure code"
            raise ValueError(msg)

        if self.status is AgenticReviewStatus.INPUT_REJECTED:
            if (
                self.validation is not None
                or self.invocation_id is not None
                or self.invocation_path is not None
            ):
                msg = "input_rejected cannot contain invocation provenance"
                raise ValueError(msg)
        elif self.status in {
            AgenticReviewStatus.VALIDATION_FAILED,
            AgenticReviewStatus.UNAVAILABLE,
        }:
            if self.invocation_id is None or self.invocation_path is None:
                msg = "provider-started result requires durable provenance"
                raise ValueError(msg)
            if (
                self.status is AgenticReviewStatus.UNAVAILABLE
                and self.validation is not None
            ):
                msg = "unavailable result cannot contain validation"
                raise ValueError(msg)
            if (
                self.validation is not None
                and self.validation.status is not ReviewValidationStatus.REJECTED
            ):
                msg = "validation_failed result cannot contain accepted validation"
                raise ValueError(msg)
        elif self.status is AgenticReviewStatus.PROVENANCE_FAILED and (
            self.invocation_id is None or self.invocation_path is not None
        ):
            msg = "provenance_failed requires identity without a durable path"
            raise ValueError(msg)
        return self


def _snapshot_model[ModelT: BaseModel](
    value: object,
    model_type: type[ModelT],
) -> object:
    if isinstance(value, model_type):
        payload = deepcopy(value.model_dump(mode="python"))
        return model_type.model_validate(payload)
    return deepcopy(value)


def _canonical_target(
    evidence: tuple[Evidence, ...],
    *,
    asset_name: str,
    partition: str,
) -> Evidence:
    """Evidence 튜플에서 null_spike 프로파일 타겟을 정확히 하나 추출한다.

    0개이거나 2개 이상일 경우 결정론적 비교의 모호성을 방지하기 위해
    ValueError를 발생시킨다.
    """
    profile_targets = [
        item
        for item in evidence
        if item.source is EvidenceSource.PROFILE
        and item.payload.get("rule") == "null_spike"
    ]
    targets = [
        item
        for item in profile_targets
        if item.asset_name == asset_name and item.partition == partition
    ]
    if len(targets) != 1:
        if profile_targets and not targets:
            msg = "canonical target evidence identity must match the incident"
            raise ValueError(msg)
        msg = "exactly one canonical null_spike target evidence is required"
        raise ValueError(msg)
    return targets[0]


def _target_column(evidence: Evidence) -> str:
    """Canonical target evidence 페이로드에서 검토 대상 컬럼명을 추출하고 정규화한다."""
    column = evidence.payload.get("column")
    if not isinstance(column, str) or not column.strip():
        msg = "canonical target column must be a non-empty string"
        raise ValueError(msg)
    return column.strip()


def _null_spike_facts(evidence: Evidence) -> NullSpikeFacts:
    """Canonical target evidence 페이로드에서 4대 수치 팩트를 추출하여 모델로 조립한다.

    baseline_null_rate, current_null_rate, delta, threshold가 모두 유한한(finite)
    수치여야 하며 불리언은 거부된다.
    """
    values: dict[str, float] = {}
    for field_name in (
        "baseline_null_rate",
        "current_null_rate",
        "delta",
        "threshold",
    ):
        raw_value = evidence.payload.get(field_name)
        if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
            msg = f"canonical target {field_name} must be numeric"
            raise ValueError(msg)
        value = float(raw_value)
        if not isfinite(value):
            msg = f"canonical target {field_name} must be finite"
            raise ValueError(msg)
        values[field_name] = value
    return NullSpikeFacts(**values)


def _validate_canonical_json(value: object) -> None:
    try:
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as error:
        msg = "evidence payload must be canonical-JSON serializable"
        raise ValueError(msg) from error


def _non_empty(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        msg = f"{field_name} must be non-empty"
        raise ValueError(msg)
    return normalized


def _normalized_unique_strings(
    values: tuple[str, ...],
    *,
    field_name: str,
) -> tuple[str, ...]:
    normalized = tuple(_non_empty(value, field_name=field_name) for value in values)
    if len(normalized) != len(set(normalized)):
        msg = f"{field_name} must contain unique values"
        raise ValueError(msg)
    return normalized
