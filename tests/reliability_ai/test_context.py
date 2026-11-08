"""Bounded Review Context의 provenance, gap과 replay contract tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from hmda_reliability.reliability.contracts import Evidence, EvidenceSource
from hmda_reliability.reliability_ai import contracts
from hmda_reliability.reliability_ai.context import (
    build_bounded_review_context,
    project_remote_output,
)
from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry
from hmda_reliability.reliability_ai.prompt import build_canonical_input
from hmda_reliability.runtime_ai.contracts import ToolCall, ToolCallFunction

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


@pytest.mark.parametrize(
    "asset_name",
    [
        "/home/private/context.csv",
        "file:///home/private/context.csv",
        "metadata_file:///home/private/context.csv",
    ],
)
def test_provider_and_remote_projection_remove_nested_private_material(
    null_spike_review_material: NullSpikeReviewMaterial,
    asset_name: str,
) -> None:
    evidence = _surrounding_evidence(null_spike_review_material)
    evidence[1] = evidence[1].model_copy(
        update={
            "summary": "Inspect /opt/private/source.csv and C:\\private\\source.csv",
            "asset_name": asset_name,
            "payload": {
                "columns": ["income"],
                "column_types": {
                    "income": "DOUBLE",
                    "credentials": {"token": "hidden"},
                },
                "table_name": "/var/private/table.csv",
            },
        }
    )
    review_input = _review_input(null_spike_review_material, evidence)
    review_input = review_input.model_copy(
        update={
            "draft": review_input.draft.model_copy(
                update={
                    "rca_summary": "Inspect /srv/private/raw.csv",
                }
            ),
        }
    )

    canonical = build_canonical_input(review_input)
    record, tool_output = ToolRegistry.from_review_input(review_input).execute(
        ToolCall(
            id="contextual-path",
            function=ToolCallFunction(
                name="get_incident_evidence", arguments='{"evidence_id":"ev-table"}'
            ),
        )
    )
    assert record.status == "success"
    remote = project_remote_output(
        {
            "result": canonical,
            "manifest_path": "/opt/private/manifest.json",
            "response_paths": ["/var/private/raw.txt"],
        }
    )

    for payload in (canonical, remote, json.loads(tool_output)):
        encoded = json.dumps(payload)
        assert "private" not in encoded.replace("[private-path]", "")
        assert "hidden" not in encoded
        assert "credentials" not in encoded
    facts = canonical["deterministic_facts"]
    assert isinstance(facts, dict)
    assert facts["current_null_rate"] == 0.21
    assert "manifest_path" not in remote


def test_evidence_metadata_shapes_exclude_nested_raw_rows(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    evidence = _surrounding_evidence(null_spike_review_material)
    raw_rows = [{"applicant_id": "SYNTHETIC-ROW", "income": 12345}]
    evidence[1] = evidence[1].model_copy(
        update={
            "payload": {
                "column_types": {"income": "DOUBLE", "raw_rows": raw_rows},
                "columns": [
                    {
                        "name": "income",
                        "type": "DOUBLE",
                        "nullable": "YES",
                        "raw_rows": raw_rows,
                    },
                    {"raw_rows": raw_rows},
                ],
                "schema_hash": {"raw_rows": raw_rows},
            }
        }
    )
    evidence.append(
        Evidence(
            evidence_id="catalog-shapes",
            source=EvidenceSource.CATALOG,
            asset_name="raw.hmda_loans",
            partition="2025",
            observed_at=evidence[1].observed_at,
            summary="Catalog metadata",
            payload={
                "upstream_assets": ["source.hmda", {"raw_rows": raw_rows}],
                "lineage": [
                    {
                        "from": "source.hmda",
                        "to": "raw.hmda_loans",
                        "raw_rows": raw_rows,
                    }
                ],
            },
        )
    )
    review_input = _review_input(null_spike_review_material, evidence)
    canonical = build_canonical_input(review_input)
    registry = ToolRegistry.from_review_input(review_input)
    outputs = []
    for item in (evidence[1], evidence[-1]):
        record, output = registry.execute(
            ToolCall(
                id=item.evidence_id,
                function=ToolCallFunction(
                    name="get_incident_evidence",
                    arguments=json.dumps({"evidence_id": item.evidence_id}),
                ),
            )
        )
        assert record.status == "success"
        outputs.append(json.loads(output))
    for projected in (canonical, *outputs, project_remote_output({"input": canonical})):
        assert "SYNTHETIC-ROW" not in json.dumps(projected)
        assert "raw_rows" not in json.dumps(projected)
    assert outputs[0]["payload"] == {
        "column_types": {"income": "DOUBLE"},
        "columns": [{"name": "income", "type": "DOUBLE", "nullable": "YES"}],
    }
    assert outputs[1]["payload"] == {
        "upstream_assets": ["source.hmda"],
        "lineage": [{"from": "source.hmda", "to": "raw.hmda_loans"}],
    }
