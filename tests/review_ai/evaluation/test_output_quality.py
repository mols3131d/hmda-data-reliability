"""독립 수치 oracle과 합성 prose 결함은 structured acceptance와 구별한다.

이 corpus는 live 출력이나 human rubric 평가가 아니다. 의미 품질 label은
검토자가 참고할 고정 annotation이며 자동 semantic classifier로 사용하지 않는다.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from hmda_reliability.reliability import (
    DetectionRequest,
    ProfileSnapshot,
    RemediationDraftRequest,
    create_remediation_draft,
    detect_basic_incidents,
)
from hmda_reliability.reliability.detection.thresholds import DetectionThresholds
from hmda_reliability.review_ai.context import build_bounded_review_context
from hmda_reliability.review_ai.contracts import (
    AgenticReviewInput,
    AgenticReviewOutput,
    PromptIdentity,
)
from hmda_reliability.review_ai.prompt.legacy import render_review_prompt
from hmda_reliability.review_ai.validator import validate_agentic_review

pytestmark = pytest.mark.unit

_CORPUS_PATH = Path(__file__).with_name("fixtures") / "output_quality_v1.json"
_CORPUS = json.loads(_CORPUS_PATH.read_text(encoding="utf-8"))
_CASES = _CORPUS["cases"]
_ACCEPTED_CONTROLS = [
    pytest.param(case, control, id=f"{case['case_id']}/{control['control_id']}")
    for case in _CASES
    for control in case["controls"]
    if control["expected_structured_validation"] == "accepted"
]
_BACKFILL = (
    "원인 확인과 사람의 승인 후 2025 partition backfill의 필요성 및 범위를 검토한다."
)


def _input(case: dict[str, Any]) -> AgenticReviewInput:
    return AgenticReviewInput.model_validate(case["review_input"])


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case["case_id"])
def test_portable_input_replays_real_detection_and_draft_contracts(
    case: dict[str, Any],
) -> None:
    stored = _input(case)
    snapshots = [
        ProfileSnapshot(
            snapshot_id=f"profile-{role}-2025",
            asset_name="raw.hmda_loans",
            partition="2025",
            observed_at=datetime(2026, 8, 27, tzinfo=UTC),
            row_count=100,
            null_rates={"income": float(case["profile_pair"][f"{role}_null_rate"])},
            schema_hash="sha256:stable",
            freshness_at=None,
            freshness_status="unavailable",
        )
        for role in ("baseline", "current")
    ]
    (detection,) = detect_basic_incidents(
        DetectionRequest(
            baseline=snapshots[0],
            current=snapshots[1],
            thresholds=DetectionThresholds(
                null_spike_delta=float(case["profile_pair"]["threshold"])
            ),
        )
    )
    draft = create_remediation_draft(
        RemediationDraftRequest(
            incident=detection.incident,
            evidence=detection.evidence,
        )
    )
    evidence = [detection.evidence, *stored.evidence[1:]]
    references = [item.evidence_id for item in evidence]
    incident_payload = detection.incident.model_dump(mode="python")
    incident_payload["evidence_refs"] = references
    draft_payload = draft.model_dump(mode="python")
    draft_payload["evidence_refs"] = references
    if case["case_id"] == "null-spike-supplied-context-backfill":
        # 명시적인 advisory 변형이며 null_spike 기본 초안의 생성 결과는 아니다.
        draft_payload.update(backfill_actions=[_BACKFILL], requires_approval=True)

    rebuilt = AgenticReviewInput(
        incident=incident_payload,
        evidence=evidence,
        draft=draft_payload,
        prompt_identity=PromptIdentity(version="v2"),
        project_revision="fixture-output-quality-v1",
    )

    assert stored == rebuilt
    assert AgenticReviewInput.model_validate_json(stored.model_dump_json()) == stored
    assert stored.target_column == "income"


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case["case_id"])
def test_numeric_oracle_uses_decimal_rates_and_distinct_percentage_point_units(
    case: dict[str, Any],
) -> None:
    raw = case["profile_pair"]
    baseline = Decimal(raw["baseline_null_rate"])
    current = Decimal(raw["current_null_rate"])
    threshold = Decimal(raw["threshold"])
    expected = case["oracle"]["numeric"]
    hundred = Decimal(100)

    assert Decimal(expected["baseline_percent"]) == baseline * hundred
    assert Decimal(expected["current_percent"]) == current * hundred
    assert (
        Decimal(expected["delta_percentage_points"]) == (current - baseline) * hundred
    )
    assert Decimal(expected["threshold_percentage_points"]) == threshold * hundred
    if baseline == 0:
        assert expected["relative_increase_percent"] is None
    else:
        assert Decimal(expected["relative_increase_percent"]) == (
            (current - baseline) / baseline * hundred
        )

    facts = _input(case).deterministic_facts
    assert facts.baseline_null_rate == float(baseline)
    assert facts.current_null_rate == float(current)
    assert facts.threshold == float(threshold)
    # Decimal 정답을 binary float의 생성 과정과 구별한다.
    assert facts.delta == pytest.approx(float(current - baseline))


@pytest.mark.parametrize("case", _CASES, ids=lambda case: case["case_id"])
def test_context_oracle_preserves_supplied_facts_and_unconfirmed_root_cause(
    case: dict[str, Any],
) -> None:
    context = build_bounded_review_context(_input(case))

    assert [
        {
            "evidence_id": item.evidence_id,
            "source": item.source.value,
            "facts": item.facts,
        }
        for item in context.selected_evidence
    ] == case["oracle"]["expected_context_evidence"]
    assert {gap.topic for gap in context.gaps if gap.kind == "missing_evidence"} == set(
        case["oracle"]["missing_context_sources"]
    )
    assert {gap.topic for gap in context.gaps if gap.kind == "unconfirmed_context"} == {
        "root_cause"
    }


def test_supplied_sources_and_backfill_case_are_distinct_from_missing_cases() -> None:
    missing, zero, supplied = map(_input, _CASES)

    assert missing.draft.backfill_actions == zero.draft.backfill_actions == []
    assert not missing.draft.requires_approval
    assert not zero.draft.requires_approval
    assert supplied.draft.backfill_actions == [_BACKFILL]
    assert supplied.draft.requires_approval
    context = build_bounded_review_context(supplied)
    assert {item.source.value for item in context.selected_evidence} == {
        "profile",
        "table_metadata",
        "catalog",
        "dbt_artifact",
    }
    assert context.selected_evidence[-1].facts["status"] == "fail"
    assert [(gap.kind.value, gap.topic) for gap in context.gaps] == [
        ("unconfirmed_context", "root_cause")
    ]


@pytest.mark.parametrize(("case", "control"), _ACCEPTED_CONTROLS)
def test_known_prose_failures_and_good_controls_all_pass_current_structured_guard(
    case: dict[str, Any], control: dict[str, Any]
) -> None:
    """잘못된 prose의 accepted는 guard 한계이며 품질 합격 증거가 아니다."""
    review_input = _input(case)
    output = AgenticReviewOutput.model_validate(control["output"])

    assert output.incident_id == review_input.incident.incident_id
    assert output.target_column == review_input.target_column
    assert output.deterministic_facts == review_input.deterministic_facts
    validation = validate_agentic_review(review_input, output)

    assert validation.status == "accepted"
    assert validation.violations == ()
    assert validation.policy_id == "structured-fact-validation-v1"


def test_structured_fact_mismatch_is_rejected_as_contrast_to_prose_failures() -> None:
    case = _CASES[0]
    control = next(
        item
        for item in case["controls"]
        if item["control_id"] == "structured-fact-mismatch"
    )
    review_input = _input(case)
    output = AgenticReviewOutput.model_validate(control["output"])

    validation = validate_agentic_review(review_input, output)

    assert output.deterministic_facts.current_null_rate == 0.31
    assert validation.status == "rejected"
    assert validation.violations == ("deterministic_contradiction",)


def test_v2_example_copy_exact_match_is_only_a_test_signal() -> None:
    case = _CASES[0]
    copied = next(
        item for item in case["controls"] if item["control_id"] == "copied-example"
    )
    good = next(item for item in case["controls"] if item["control_id"] == "good")
    descriptions = set(_CORPUS["v2_example_descriptions"])
    system_prompt = (
        render_review_prompt(_input(case), max_prompt_bytes=65_536).messages[0].content
    )

    assert len(descriptions) == 4
    assert all(description in system_prompt for description in descriptions)
    assert {
        item["description"] for item in copied["output"]["utility_contributions"]
    } == descriptions
    assert not descriptions.intersection(
        item["description"] for item in good["output"]["utility_contributions"]
    )
