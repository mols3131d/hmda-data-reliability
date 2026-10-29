"""Immutable current input and deterministic fact contract tests."""

from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from hmda_reliability.review_ai import contracts as contracts_module

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.unit


def test_current_input_requires_no_prompt_identity(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    payload = dict(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="current-input",
    )
    review_input = contracts_module.AgenticReviewInput.model_validate(payload)
    assert "prompt_identity" not in review_input.model_dump()
    with pytest.raises(ValidationError, match="extra_forbidden"):
        contracts_module.AgenticReviewInput.model_validate(
            payload | {"prompt_identity": {"version": "v1"}}
        )


def _review_input(
    material: NullSpikeReviewMaterial,
) -> contracts_module.AgenticReviewInput:
    return contracts_module.AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="e09c54b",
    )


def test_detector_evidence_identifies_the_null_spike_rule(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    assert null_spike_review_material.detection.evidence.payload["rule"] == "null_spike"


def test_input_derives_one_canonical_target_and_snapshots_nested_values(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    source_payload = deepcopy(material.detection.evidence.payload)

    review_input = _review_input(material)

    material.detection.incident.evidence_refs.append("caller-mutation")
    material.detection.evidence.payload["delta"] = 0.99
    material.draft.recommended_actions.append("caller-mutation")

    assert review_input.target_column == "income"
    assert review_input.deterministic_facts == contracts_module.NullSpikeFacts(
        baseline_null_rate=0.01,
        current_null_rate=0.21,
        delta=0.21 - 0.01,
        threshold=0.10,
    )
    assert review_input.incident.evidence_refs == [
        material.detection.evidence.evidence_id
    ]
    assert review_input.evidence[0].payload == source_payload
    assert "caller-mutation" not in review_input.draft.recommended_actions


def test_input_accepts_referenced_context_evidence_from_related_asset(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    target = material.detection.evidence
    context = target.model_copy(
        update={
            "evidence_id": "related-table-metadata",
            "source": contracts_module.EvidenceSource.TABLE_METADATA,
            "asset_name": "HMDA_LOAN",
            "partition": "2024",
            "summary": "Related table metadata",
            "payload": {"table_name": "HMDA_LOAN", "columns": ["income"]},
        }
    )
    incident = material.detection.incident.model_copy(
        update={"evidence_refs": [target.evidence_id, context.evidence_id]}
    )
    draft = material.draft.model_copy(
        update={"evidence_refs": [target.evidence_id, context.evidence_id]}
    )

    review_input = contracts_module.AgenticReviewInput(
        incident=incident,
        evidence=[target, context],
        draft=draft,
        project_revision="e09c54b",
    )

    assert review_input.target_column == "income"
    assert {item.evidence_id for item in review_input.evidence} == {
        target.evidence_id,
        context.evidence_id,
    }
    assert review_input.evidence[1].asset_name == "HMDA_LOAN"
    assert review_input.evidence[1].partition == "2024"


def test_input_accepts_related_profile_evidence_as_context(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    target = material.detection.evidence
    context = target.model_copy(
        update={
            "evidence_id": "related-null-spike-profile",
            "asset_name": "HMDA_LOAN",
            "partition": "2024",
            "summary": "Related asset null-spike profile",
        }
    )
    evidence_refs = [target.evidence_id, context.evidence_id]
    incident = material.detection.incident.model_copy(
        update={"evidence_refs": evidence_refs}
    )
    draft = material.draft.model_copy(update={"evidence_refs": evidence_refs})

    review_input = contracts_module.AgenticReviewInput(
        incident=incident,
        evidence=[target, context],
        draft=draft,
        project_revision="e09c54b",
    )

    assert review_input.target_column == "income"
    assert review_input.evidence[1].evidence_id == context.evidence_id
    assert review_input.evidence[1].asset_name == "HMDA_LOAN"
    assert review_input.evidence[1].partition == "2024"


def test_input_rejects_canonical_target_from_another_asset(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    target = material.detection.evidence.model_copy(update={"asset_name": "HMDA_LOAN"})
    incident = material.detection.incident.model_copy(
        update={"evidence_refs": [target.evidence_id]}
    )
    draft = material.draft.model_copy(update={"evidence_refs": [target.evidence_id]})

    with pytest.raises(ValidationError, match="canonical target evidence identity"):
        contracts_module.AgenticReviewInput(
            incident=incident,
            evidence=[target],
            draft=draft,
            project_revision="e09c54b",
        )


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_evidence",
        "duplicate_evidence",
        "draft_partition_mismatch",
        "unsupported_type",
        "missing_rule",
        "missing_numeric_fact",
    ],
)
def test_input_rejects_identity_linkage_and_canonical_target_errors(
    null_spike_review_material: NullSpikeReviewMaterial,
    mutation: str,
) -> None:
    material = null_spike_review_material
    incident = material.detection.incident
    evidence = [material.detection.evidence]
    draft = material.draft

    if mutation == "missing_evidence":
        evidence = []
    elif mutation == "duplicate_evidence":
        evidence = [material.detection.evidence, material.detection.evidence]
    elif mutation == "draft_partition_mismatch":
        draft = draft.model_copy(update={"partition": "2024"})
    elif mutation == "unsupported_type":
        incident = incident.model_copy(update={"incident_type": "volume_drop"})
        draft = draft.model_copy(update={"incident_type": "volume_drop"})
    elif mutation == "missing_rule":
        payload = dict(material.detection.evidence.payload)
        payload.pop("rule")
        evidence = [material.detection.evidence.model_copy(update={"payload": payload})]
    elif mutation == "missing_numeric_fact":
        payload = dict(material.detection.evidence.payload)
        payload.pop("threshold")
        evidence = [material.detection.evidence.model_copy(update={"payload": payload})]

    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewInput(
            incident=incident,
            evidence=evidence,
            draft=draft,
            project_revision="e09c54b",
        )


def test_input_rejects_empty_revision(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    material = null_spike_review_material
    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            project_revision="   ",
        )
