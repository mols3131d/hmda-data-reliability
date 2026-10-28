"""실패 응답 원문 없이 남기는 bounded parse diagnosis."""

from __future__ import annotations

import json
from typing import Literal

from pydantic import Field, ValidationError, field_validator

from hmda_reliability.reliability.contracts.base import ReliabilityContract
from hmda_reliability.review_ai.contracts import AgenticReviewOutput

_PATH_FIELDS = frozenset(
    {
        "incident_id",
        "incident_type",
        "target_column",
        "deterministic_facts",
        "baseline_null_rate",
        "current_null_rate",
        "delta",
        "threshold",
        "review_summary",
        "evidence_used",
        "findings",
        "uncertainties",
        "advisory_recommendation",
        "utility_contributions",
        "kind",
        "description",
        "evidence_refs",
        "priority",
        "item",
        "unknown",
    }
)


class ResponseValidationIssue(ReliabilityContract):
    field_path: str = Field(min_length=1, max_length=128)
    code: Literal[
        "type_invalid",
        "missing_field",
        "extra_field",
        "conditional_invalid",
        "value_invalid",
    ]

    @field_validator("field_path")
    @classmethod
    def _allowlist_path(cls, value: str) -> str:
        parts = value.split(".")
        if len(parts) > 4 or any(part not in _PATH_FIELDS for part in parts):
            raise ValueError(
                "diagnostic field path must contain only known schema fields"
            )
        return value


class ReviewResponseDiagnostics(ReliabilityContract):
    """분류만 보존하며 입력값, exception message와 임의 field 이름은 제외한다."""

    kind: Literal[
        "response_content_empty", "json_syntax_invalid", "schema_validation_failed"
    ]
    issues: tuple[ResponseValidationIssue, ...] = Field(default=(), max_length=8)


def parse_review_response(
    content: str,
) -> tuple[AgenticReviewOutput | None, ReviewResponseDiagnostics | None]:
    """출력 계약을 완화하지 않고 실패 단계와 정제된 field/code만 반환한다."""
    if not content.strip():
        return None, ReviewResponseDiagnostics(kind="response_content_empty")
    try:
        payload = json.loads(content)
    except (ValueError, RecursionError):
        return None, ReviewResponseDiagnostics(kind="json_syntax_invalid")
    try:
        return AgenticReviewOutput.model_validate(payload), None
    except ValidationError as error:
        issues = []
        # Pydantic의 input/context/message에는 응답 원문이 포함될 수 있다.
        for detail in error.errors(
            include_input=False, include_context=False, include_url=False
        )[:8]:
            path = (
                ".".join(
                    "item"
                    if isinstance(part, int)
                    else part
                    if part in _PATH_FIELDS
                    else "unknown"
                    for part in detail["loc"][:4]
                )
                or "unknown"
            )
            error_type = detail["type"]
            code = "value_invalid"
            if error_type.endswith("_type"):
                code = "type_invalid"
            elif error_type == "missing":
                code = "missing_field"
            elif error_type == "extra_forbidden":
                code = "extra_field"
            elif error_type == "value_error" and path == "utility_contributions.item":
                code = "conditional_invalid"
            issues.append(
                ResponseValidationIssue.model_validate(
                    {"field_path": path, "code": code}
                )
            )
        return None, ReviewResponseDiagnostics(
            kind="schema_validation_failed", issues=tuple(issues)
        )
    except RecursionError:
        return None, ReviewResponseDiagnostics(kind="schema_validation_failed")
