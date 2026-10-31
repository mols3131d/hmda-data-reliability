"""Incident 주변의 bounded, provenance-aware review context를 생성한다."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from copy import deepcopy
from datetime import datetime
from enum import StrEnum
from math import isfinite

from pydantic import Field, field_validator

from hmda_reliability.reliability.contracts import Evidence, EvidenceSource
from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.review_ai.contracts import AgenticReviewInput

_DEFAULT_REQUIRED_SOURCES = (
    EvidenceSource.TABLE_METADATA,
    EvidenceSource.CATALOG,
    EvidenceSource.DBT_ARTIFACT,
)
_SOURCE_PRIORITY = {
    EvidenceSource.PROFILE: 0,
    EvidenceSource.TABLE_METADATA: 1,
    EvidenceSource.CATALOG: 2,
    EvidenceSource.DBT_ARTIFACT: 3,
    EvidenceSource.ORCHESTRATION: 4,
}
_PAYLOAD_ALLOWLIST = {
    EvidenceSource.PROFILE: (
        "rule",
        "column",
        "baseline_null_rate",
        "current_null_rate",
        "delta",
        "threshold",
        "row_count",
        "schema_hash",
    ),
    EvidenceSource.TABLE_METADATA: (
        "table_name",
        "columns",
        "column_types",
        "partition_column",
        "schema_hash",
    ),
    EvidenceSource.CATALOG: (
        "related_assets",
        "upstream_assets",
        "downstream_assets",
        "lineage",
    ),
    EvidenceSource.DBT_ARTIFACT: (
        "model",
        "test_name",
        "status",
        "artifact_id",
        "projection_id",
    ),
    EvidenceSource.ORCHESTRATION: (
        "dag_id",
        "task_id",
        "run_id",
        "status",
    ),
}


class ReviewContextGapKind(StrEnum):
    MISSING_EVIDENCE = "missing_evidence"
    UNCONFIRMED_CONTEXT = "unconfirmed_context"


class ReviewContextGap(ReliabilityContract):
    kind: ReviewContextGapKind
    topic: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=512)


class ReviewContextProvenance(ReliabilityContract):
    evidence_id: str = Field(min_length=1, max_length=256)
    source: EvidenceSource
    asset_name: str = Field(min_length=1, max_length=256)
    partition: str = Field(min_length=1, max_length=256)
    observed_at: datetime


class BoundedReviewEvidence(ReliabilityContract):
    evidence_id: str = Field(min_length=1, max_length=256)
    source: EvidenceSource
    summary: str = Field(min_length=1, max_length=1024)
    facts: dict[str, object] = Field(max_length=16)
    provenance: ReviewContextProvenance

    @field_validator("facts", mode="before")
    @classmethod
    def _validate_fact_size(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        if len(_canonical_json_bytes(value)) > 4_096:
            msg = "bounded evidence facts exceed the per-evidence limit"
            raise ValueError(msg)
        return deepcopy(value)


class BoundedReviewContext(ReliabilityContract):
    incident_id: str = Field(min_length=1, max_length=256)
    selected_evidence: tuple[BoundedReviewEvidence, ...] = Field(
        min_length=1,
        max_length=16,
    )
    gaps: tuple[ReviewContextGap, ...] = Field(max_length=32)
    digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class ReviewContextTooLargeError(ValueError):
    """직렬화된 bounded context가 설정된 크기 한도를 넘을 때 발생한다."""


def build_bounded_review_context(
    review_input: AgenticReviewInput,
    *,
    required_sources: Sequence[EvidenceSource] = _DEFAULT_REQUIRED_SOURCES,
    max_evidence: int = 8,
    max_context_bytes: int = 16_384,
) -> BoundedReviewContext:
    """입력 Evidence를 제한된 provenance-aware context로 투영한다."""

    if not 1 <= max_evidence <= 16:
        msg = "max_evidence must be between 1 and 16"
        raise ValueError(msg)
    if not 4_096 <= max_context_bytes <= 1_048_576:
        msg = "max_context_bytes must be between 4096 and 1048576"
        raise ValueError(msg)

    ordered = sorted(
        review_input.evidence,
        key=lambda item: (
            0
            if item.source is EvidenceSource.PROFILE
            and item.payload.get("rule") == "null_spike"
            and item.asset_name == review_input.incident.asset_name
            and item.partition == review_input.incident.partition
            else 1,
            _SOURCE_PRIORITY[item.source],
            item.evidence_id,
        ),
    )
    selected = tuple(_project_evidence(item) for item in ordered[:max_evidence])
    gaps = list(_missing_source_gaps(review_input, required_sources))
    if len(ordered) > max_evidence:
        omitted = len(ordered) - max_evidence
        gaps.append(
            ReviewContextGap(
                kind=ReviewContextGapKind.UNCONFIRMED_CONTEXT,
                topic="bounded_selection",
                description=f"제공된 근거 {omitted}개가 개수 제한으로 제외되었습니다.",
            )
        )
    gaps.append(
        ReviewContextGap(
            kind=ReviewContextGapKind.UNCONFIRMED_CONTEXT,
            topic="root_cause",
            description="제공된 근거만으로는 근본 원인을 확정할 수 없습니다.",
        )
    )

    unsigned = {
        "incident_id": review_input.incident.incident_id,
        "selected_evidence": [item.model_dump(mode="json") for item in selected],
        "gaps": [item.model_dump(mode="json") for item in gaps],
    }
    digest = f"sha256:{hashlib.sha256(_canonical_json_bytes(unsigned)).hexdigest()}"
    context = BoundedReviewContext(
        incident_id=review_input.incident.incident_id,
        selected_evidence=selected,
        gaps=tuple(gaps),
        digest=digest,
    )
    if len(_canonical_json_bytes(context.model_dump(mode="json"))) > max_context_bytes:
        raise ReviewContextTooLargeError(
            "bounded review context exceeds max_context_bytes"
        )
    return context


def _project_evidence(evidence: Evidence) -> BoundedReviewEvidence:
    facts: dict[str, object] = {}
    for field_name in _PAYLOAD_ALLOWLIST[evidence.source]:
        if field_name not in evidence.payload:
            continue
        bounded = _bound_json_value(evidence.payload[field_name])
        if bounded is not _SKIP:
            facts[field_name] = bounded
    return BoundedReviewEvidence(
        evidence_id=evidence.evidence_id,
        source=evidence.source,
        summary=(evidence.summary.strip() or "근거 요약이 제공되지 않았습니다.")[:1024],
        facts=facts,
        provenance=ReviewContextProvenance(
            evidence_id=evidence.evidence_id,
            source=evidence.source,
            asset_name=evidence.asset_name,
            partition=evidence.partition,
            observed_at=evidence.observed_at,
        ),
    )


def _missing_source_gaps(
    review_input: AgenticReviewInput,
    required_sources: Sequence[EvidenceSource],
) -> tuple[ReviewContextGap, ...]:
    available = {item.source for item in review_input.evidence}
    return tuple(
        ReviewContextGap(
            kind=ReviewContextGapKind.MISSING_EVIDENCE,
            topic=source.value,
            description=f"이번 검토에는 {source.value} 근거가 제공되지 않았습니다.",
        )
        for source in dict.fromkeys(required_sources)
        if source not in available
    )


_SKIP = object()


def _bound_json_value(value: object, *, max_bytes: int = 1_024) -> object:
    if value is None or isinstance(value, (str, bool, int)):
        bounded = value[:512] if isinstance(value, str) else value
        return bounded if len(_canonical_json_bytes(bounded)) <= max_bytes else _SKIP
    if isinstance(value, float):
        return value if isfinite(value) else _SKIP
    if isinstance(value, list):
        bounded_items: list[object] = []
        for item in value[:32]:
            bounded = _bound_json_value(item, max_bytes=max_bytes)
            if bounded is not _SKIP:
                bounded_items.append(bounded)
        return (
            bounded_items
            if len(_canonical_json_bytes(bounded_items)) <= max_bytes
            else _SKIP
        )
    if isinstance(value, dict):
        bounded_mapping: dict[str, object] = {}
        for key in sorted(value)[:32]:
            bounded = _bound_json_value(value[key], max_bytes=max_bytes)
            if bounded is not _SKIP:
                bounded_mapping[str(key)] = bounded
        return (
            bounded_mapping
            if len(_canonical_json_bytes(bounded_mapping)) <= max_bytes
            else _SKIP
        )
    return _SKIP


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
        default=_json_default,
    ).encode("utf-8")


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    msg = f"unsupported JSON value: {type(value).__name__}"
    raise TypeError(msg)
