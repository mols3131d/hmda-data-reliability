"""제한된(bounded) agentic review를 위한 구조화된 계약 모델 정의."""

from __future__ import annotations

import json
from copy import deepcopy
from math import isfinite

from pydantic import BaseModel, Field, field_validator, model_validator

from hmda_reliability.reliability.contracts import Evidence, EvidenceSource, Incident
from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.reliability.remediation import RemediationDraft


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
