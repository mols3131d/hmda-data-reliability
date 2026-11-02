"""현재 검토의 canonical 입력과 프롬프트 계약."""

from __future__ import annotations

import json
from copy import deepcopy

from pydantic import Field

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.review_ai.context import (
    BoundedReviewContext,
    build_bounded_review_context,
)
from hmda_reliability.review_ai.contracts import AgenticReviewInput
from hmda_reliability.runtime_ai.contracts import ChatMessage


class RenderedReviewPrompt(ReliabilityContract):
    """검증 및 출처 증명에 사용되는 렌더링된 프롬프트 상태 계약.

    Attributes:
        canonical_input: 스펙의 allowlist에 따라 정제된 구조화된 입력 딕셔너리.
        canonical_json: 재생 가능한 정렬/압축 규칙이 적용된 표준 JSON 문자열.
        messages: Provider에 전달할 system/user/assistant 대화 메시지 튜플.
        prompt_digest: 렌더링된 메시지 바이트의 SHA-256 해시 (`sha256:...`).
        prompt_bytes: UTF-8 표준 직렬화된 메시지 목록의 총 바이트 수.
    """

    canonical_input: dict[str, object]
    canonical_json: str
    messages: tuple[ChatMessage, ...]
    prompt_digest: str
    prompt_bytes: int = Field(gt=0)
    context: BoundedReviewContext | None = None


class PromptTooLargeError(ValueError):
    """렌더링된 메시지가 설정된 바이트 한도를 초과할 때 발생하는 예외."""

    def __init__(self, *, actual_bytes: int, max_bytes: int) -> None:
        super().__init__("rendered prompt exceeds max_prompt_bytes")
        self.actual_bytes = actual_bytes
        self.max_bytes = max_bytes


def build_canonical_input(
    review_input: AgenticReviewInput,
    *,
    context: BoundedReviewContext | None = None,
) -> dict[str, object]:
    """스펙에서 허용된 필드만 추출하고 evidence를 결정론적으로 정렬한다.

    신뢰할 수 없는 원천 객체로부터 지정된 allowlist 필드만 복사 투영하여
    프롬프트 크기 제어와 불필요한 메타데이터 유출을 방지한다.
    Evidence 목록은 `evidence_id` 기준 사전순으로 정렬되어 입력 순서에 무관한
    동일 다이제스트 계산을 보장한다.
    """

    incident = review_input.incident.model_dump(mode="json")
    draft = review_input.draft.model_dump(mode="json")
    facts = review_input.deterministic_facts.model_dump(mode="json")
    active_context = context or build_bounded_review_context(review_input)
    evidence = [
        item.model_dump(mode="json") for item in active_context.selected_evidence
    ]
    selected_evidence_ids = {str(item["evidence_id"]) for item in evidence}
    draft["evidence_refs"] = [
        evidence_id
        for evidence_id in draft["evidence_refs"]
        if evidence_id in selected_evidence_ids
    ]
    return {
        "incident": _pick(
            incident,
            "incident_id",
            "incident_type",
            "asset_name",
            "partition",
            "status",
            "severity",
        ),
        "evidence": [
            item for item in sorted(evidence, key=lambda item: str(item["evidence_id"]))
        ],
        "draft": _pick(
            draft,
            "incident_id",
            "incident_type",
            "asset_name",
            "partition",
            "rca_summary",
            "evidence_refs",
            "affected_assets",
            "recommended_actions",
            "dbt_test_suggestions",
            "backfill_actions",
            "validation_actions",
            "requires_approval",
        ),
        "deterministic_facts": {
            "target_column": review_input.target_column,
            **facts,
        },
        "review_context": active_context.model_dump(mode="json"),
    }


def canonical_json_bytes(value: object) -> bytes:
    """결정론적 재생(replay)을 위해 JSON 값을 표준 바이트로 직렬화한다.

    키 정렬, 압축된 구분자, UTF-8 인코딩 및 NaN 방지를 강제한다.
    """

    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _pick(payload: dict[str, object], *fields: str) -> dict[str, object]:
    return {field: deepcopy(payload[field]) for field in fields}
