"""Snapshot input, advisory output, and typed result contract tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from hmda_reliability.review_ai import contracts as contracts_module

from .conftest import NullSpikeReviewMaterial

pytestmark = pytest.mark.unit


def _review_input(
    material: NullSpikeReviewMaterial,
) -> contracts_module.AgenticReviewInput:
    return contracts_module.AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        prompt_identity=contracts_module.PromptIdentity(),
        project_revision="e09c54b",
    )


def _output(
    review_input: contracts_module.AgenticReviewInput,
) -> contracts_module.AgenticReviewOutput:
    return contracts_module.AgenticReviewOutput(
        incident_id=review_input.incident.incident_id,
        incident_type="null_spike",
        target_column=review_input.target_column,
        deterministic_facts=review_input.deterministic_facts,
        review_summary="근거에 따르면 income null rate가 증가했다.",
        evidence_used=[review_input.evidence[0].evidence_id],
        findings=[
            contracts_module.AgenticReviewFinding(
                kind="observation",
                description="제공된 profile evidence와 draft가 일치한다.",
                evidence_refs=[review_input.evidence[0].evidence_id],
            )
        ],
        uncertainties=["Source 원인은 추가 human review가 필요하다."],
        advisory_recommendation="needs_human_review",
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
            prompt_identity=contracts_module.PromptIdentity(),
            project_revision="e09c54b",
        )


def test_input_rejects_wrong_prompt_identity_and_empty_revision(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    with pytest.raises(ValidationError):
        contracts_module.PromptIdentity.model_validate({"version": "v2"})

    material = null_spike_review_material
    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewInput(
            incident=material.detection.incident,
            evidence=[material.detection.evidence],
            draft=material.draft,
            prompt_identity=contracts_module.PromptIdentity(),
            project_revision="   ",
        )


def test_output_is_closed_bounded_and_uses_typed_values(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    review_input = _review_input(null_spike_review_material)
    output = _output(review_input)

    assert output.incident_type == "null_spike"
    assert output.findings[0].kind == "observation"
    assert output.advisory_recommendation == "needs_human_review"

    payload = output.model_dump(mode="json")
    payload["incident_type"] = "volume_drop"
    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewOutput.model_validate(payload)

    payload["incident_type"] = "null_spike"
    payload["approval"] = True
    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewOutput.model_validate(payload)

    payload.pop("approval")
    payload["review_summary"] = " "
    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewOutput.model_validate(payload)

    payload["review_summary"] = "bounded"
    payload["uncertainties"] = ["x" * 4097]
    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewOutput.model_validate(payload)

    payload["uncertainties"] = []
    payload["evidence_used"] = ["e" * 257]
    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewOutput.model_validate(payload)


def test_utility_contribution_is_structured_and_priority_is_scoped(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    review_input = _review_input(null_spike_review_material)
    evidence_id = review_input.evidence[0].evidence_id
    contribution = contracts_module.AgenticReviewUtilityContribution(
        kind="investigation_priority",
        description="먼저 income 원천 추출을 확인한다.",
        evidence_refs=[evidence_id],
        priority="high",
    )
    output = _output(review_input).model_copy(
        update={"utility_contributions": (contribution,)}
    )

    assert output.utility_contributions[0].kind == "investigation_priority"
    assert output.utility_contributions[0].priority == "high"
    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewUtilityContribution(
            kind="evidence_gap",
            description="gap",
            priority="low",
        )


def test_validation_policy_versions_restrict_active_violations() -> None:
    accepted = contracts_module.AgenticReviewValidation(
        status="accepted",
        violations=[],
    )
    rejected = contracts_module.AgenticReviewValidation(
        status="rejected",
        violations=["fabricated_evidence"],
        policy_id="structured-fact-validation-v1",
    )

    assert accepted.policy_id == "structured-fact-validation-v1"
    assert rejected.violations == ("fabricated_evidence",)

    with pytest.raises(ValidationError):
        contracts_module.AgenticReviewValidation(
            status="rejected",
            violations=["forbidden_action"],
        )

    legacy = contracts_module.AgenticReviewValidation(
        status="rejected",
        violations=["forbidden_action"],
        policy_id="forbidden-action-policy-v1",
    )
    assert legacy.violations == ("forbidden_action",)


def test_typed_result_enforces_status_specific_output_and_provenance(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    review_input = _review_input(null_spike_review_material)
    output = _output(review_input)
    validation = contracts_module.AgenticReviewValidation(
        status="accepted",
        violations=[],
    )

    accepted = contracts_module.AgenticReviewResult(
        status="accepted",
        output=output,
        validation=validation,
        invocation_id="inv-1",
        invocation_path=Path("agentic-review/invocations/inv-1.json"),
    )
    assert accepted.output == output

    for status in (
        "validation_failed",
        "unavailable",
        "input_rejected",
        "provenance_failed",
    ):
        values: dict[str, object] = {
            "status": status,
            "output": output,
            "failure_code": "expected_failure",
        }
        if status in {"validation_failed", "unavailable"}:
            values.update(
                invocation_id="inv-1",
                invocation_path=Path("agentic-review/invocations/inv-1.json"),
            )
        elif status == "provenance_failed":
            values["invocation_id"] = "inv-1"

        with pytest.raises(ValidationError):
            contracts_module.AgenticReviewResult.model_validate(values)


def test_input_models_are_frozen(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    review_input = _review_input(null_spike_review_material)

    with pytest.raises(ValidationError):
        review_input.__setattr__("project_revision", "changed")
