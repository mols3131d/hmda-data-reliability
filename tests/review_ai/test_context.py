"""Bounded Review Context의 provenance, gap과 replay contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from hmda_reliability.reliability.contracts import Evidence, EvidenceSource
from hmda_reliability.review_ai import contracts
from hmda_reliability.review_ai.context import build_bounded_review_context

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.unit


def _review_input(
    material: NullSpikeReviewMaterial,
    evidence: list[Evidence],
) -> contracts.AgenticReviewInput:
    evidence_refs = [item.evidence_id for item in evidence]
    incident = material.detection.incident.model_copy(
        update={"evidence_refs": evidence_refs}
    )
    draft = material.draft.model_copy(update={"evidence_refs": evidence_refs})
    return contracts.AgenticReviewInput(
        incident=incident,
        evidence=evidence,
        draft=draft,
        prompt_identity=contracts.PromptIdentity(),
        project_revision="utility-test-revision",
    )


def _surrounding_evidence(material: NullSpikeReviewMaterial) -> list[Evidence]:
    observed_at = datetime(2026, 8, 27, 0, 1, tzinfo=UTC)
    return [
        material.detection.evidence,
        Evidence(
            evidence_id="ev-table",
            source=EvidenceSource.TABLE_METADATA,
            asset_name="raw.hmda_loans",
            partition="2025",
            observed_at=observed_at,
            summary="Partition schema metadata",
            payload={
                "table_name": "raw.hmda_loans",
                "columns": ["income", "loan_amount"],
                "schema_hash": "sha256:table",
                "raw_log": "secret and unbounded log text",
            },
        ),
        Evidence(
            evidence_id="ev-dbt",
            source=EvidenceSource.DBT_ARTIFACT,
            asset_name="raw.hmda_loans",
            partition="2025",
            observed_at=observed_at,
            summary="Validation test result",
            payload={"test_name": "not_null_income", "status": "fail"},
        ),
    ]


@pytest.mark.parametrize(
    ("summary", "expected_summary"),
    [
        pytest.param(
            "Partition schema metadata", "Partition schema metadata", id="provided"
        ),
        pytest.param("", "근거 요약이 제공되지 않았습니다.", id="empty"),
        pytest.param(" \t\n ", "근거 요약이 제공되지 않았습니다.", id="whitespace"),
    ],
)
def test_context_selects_related_evidence_and_preserves_provenance(
    null_spike_review_material: NullSpikeReviewMaterial,
    summary: str,
    expected_summary: str,
) -> None:
    evidence = _surrounding_evidence(null_spike_review_material)
    evidence[1] = evidence[1].model_copy(update={"summary": summary})
    before = evidence[1].model_dump(mode="json")
    review_input = _review_input(null_spike_review_material, evidence)

    context = build_bounded_review_context(
        review_input,
        required_sources=(EvidenceSource.TABLE_METADATA, EvidenceSource.DBT_ARTIFACT),
    )

    assert [item.evidence_id for item in context.selected_evidence] == [
        evidence[0].evidence_id,
        "ev-table",
        "ev-dbt",
    ]
    table = context.selected_evidence[1]
    assert table.summary == expected_summary
    assert table.provenance.source is EvidenceSource.TABLE_METADATA
    assert table.provenance.partition == "2025"
    assert table.facts == {
        "columns": ["income", "loan_amount"],
        "schema_hash": "sha256:table",
        "table_name": "raw.hmda_loans",
    }
    assert "raw_log" not in table.facts
    assert evidence[1].model_dump(mode="json") == before
    assert review_input.evidence[1].summary == summary


def test_context_distinguishes_missing_evidence_from_unconfirmed_context(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    review_input = _review_input(
        null_spike_review_material,
        [null_spike_review_material.detection.evidence],
    )

    context = build_bounded_review_context(
        review_input,
        required_sources=(EvidenceSource.TABLE_METADATA, EvidenceSource.CATALOG),
    )

    assert {gap.kind for gap in context.gaps} == {
        "missing_evidence",
        "unconfirmed_context",
    }
    assert any(gap.topic == "table_metadata" for gap in context.gaps)
    assert any(gap.topic == "root_cause" for gap in context.gaps)


def test_context_is_bounded_and_replayable(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    evidence = _surrounding_evidence(null_spike_review_material)
    review_input = _review_input(null_spike_review_material, evidence)

    first = build_bounded_review_context(
        review_input,
        max_evidence=2,
        max_context_bytes=4_096,
    )
    second = build_bounded_review_context(
        review_input,
        max_evidence=2,
        max_context_bytes=4_096,
    )

    assert first == second
    assert len(first.selected_evidence) == 2
    assert first.digest.startswith("sha256:")
    assert len(first.model_dump_json().encode("utf-8")) <= 4_096
    assert any(gap.topic == "bounded_selection" for gap in first.gaps)


def test_generated_gap_descriptions_are_korean_without_translating_supplied_evidence(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    evidence = _surrounding_evidence(null_spike_review_material)
    review_input = _review_input(null_spike_review_material, evidence)
    before = review_input.model_dump(mode="json")

    context = build_bounded_review_context(
        review_input,
        required_sources=(EvidenceSource.CATALOG,),
        max_evidence=2,
    )

    assert [(gap.kind.value, gap.topic, gap.description) for gap in context.gaps] == [
        (
            "missing_evidence",
            "catalog",
            "이번 검토에는 catalog 근거가 제공되지 않았습니다.",
        ),
        (
            "unconfirmed_context",
            "bounded_selection",
            "제공된 근거 1개가 개수 제한으로 제외되었습니다.",
        ),
        (
            "unconfirmed_context",
            "root_cause",
            "제공된 근거만으로는 근본 원인을 확정할 수 없습니다.",
        ),
    ]
    assert [item.evidence_id for item in context.selected_evidence] == [
        evidence[0].evidence_id,
        "ev-table",
    ]
    assert context.selected_evidence[1].summary == "Partition schema metadata"
    assert review_input.model_dump(mode="json") == before


def test_context_always_includes_canonical_target_within_bound(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    target = null_spike_review_material.detection.evidence.model_copy(
        update={"evidence_id": "zzz-canonical-profile"}
    )
    related_profiles = [
        target.model_copy(
            update={
                "evidence_id": f"aaa-related-profile-{index:02d}",
                "asset_name": "raw.related_loans",
                "partition": "2024",
            }
        )
        for index in range(8)
    ]
    review_input = _review_input(
        null_spike_review_material,
        [*related_profiles, target],
    )

    context = build_bounded_review_context(review_input, max_evidence=8)

    selected_ids = {item.evidence_id for item in context.selected_evidence}
    assert target.evidence_id in selected_ids
    assert len(context.selected_evidence) == 8
