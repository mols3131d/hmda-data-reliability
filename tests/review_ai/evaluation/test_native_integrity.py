from dataclasses import replace

import pytest

from hmda_reliability.review_ai.evaluation.annotations import (
    check_annotation_completeness,
    check_pair_decision,
)
from hmda_reliability.review_ai.evaluation.identity import (
    CRITERIA,
    ReviewTarget,
    case_payload_digest,
    check_comparable_targets,
    review_output_digest,
)
from hmda_reliability.review_ai.staged.contracts import (
    StageAnswer,
    assemble_staged_output,
)
from tests.review_ai.test_staged_service import TEXTS

pytestmark = pytest.mark.unit


def target(**changes):
    return replace(
        ReviewTarget(
            "case",
            "1",
            "sha256:case",
            "w1",
            "rev1",
            "sha256:input",
            "sha256:out",
            "trace",
            "obs",
            "run1",
        ),
        **changes,
    )


def scores():
    return [
        dict(
            id=name,
            name=name,
            config_id=name,
            data_type="CATEGORICAL",
            value=1.0,
            string_value="1",
            comment="사람의 평가 근거",
            source="ANNOTATION",
            timestamp="2026-10-30T00:00:00Z",
            author_user_id="human",
            trace_id="trace",
            observation_id="obs",
        )
        for name in CRITERIA
    ]


def test_revision_is_provenance_and_workflow_conflict_is_blocked():
    assert (
        check_comparable_targets(
            target(), target(workflow_id="w2", project_revision="rev2")
        )
        is None
    )
    assert (
        check_comparable_targets(target(), target(output_digest="other"))
        == "workflow_output_conflict"
    )
    assert (
        check_comparable_targets(target(), target(case_digest="other"))
        == "case_mismatch"
    )


def test_case_digest_excludes_revision_and_output_digest_preserves_exact_text(
    null_spike_review_material,
):
    from hmda_reliability.review_ai.contracts import AgenticReviewInput

    material = null_spike_review_material
    source = AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        project_revision="revision",
    )
    assert case_payload_digest(source) == case_payload_digest(
        source.model_copy(update={"project_revision": "new"})
    )
    from hmda_reliability.review_ai.staged.contracts import STAGE_IDS

    output = assemble_staged_output(
        source,
        tuple(
            StageAnswer(stage_id=s, text=t)
            for s, t in zip(STAGE_IDS, TEXTS, strict=True)
        ),
    )
    altered = output.model_copy(
        update={
            "stages": (
                output.stages[0].model_copy(
                    update={"text": output.stages[0].text + " "}
                ),
                *output.stages[1:],
            )
        }
    )
    assert review_output_digest(output) != review_output_digest(altered)


def test_native_human_scores_are_order_independent():
    assert (
        check_annotation_completeness(
            target(),
            reviewer_id="human",
            config_ids={n: n for n in CRITERIA},
            scores=list(reversed(scores())),
        )
        == ()
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source", "API"),
        ("comment", " "),
        ("config_id", "other"),
        ("value", True),
        ("value", 1.5),
        ("string_value", "2"),
        ("data_type", "NUMERIC"),
        ("timestamp", None),
        ("timestamp", "unknown"),
        ("timestamp", "2026-10-30T00:00:00"),
    ],
)
def test_invalid_native_score_is_incomplete(field, value):
    records = scores()
    records[0][field] = value
    assert check_annotation_completeness(
        target(),
        reviewer_id="human",
        config_ids={n: n for n in CRITERIA},
        scores=records,
    )


def test_missing_duplicate_and_unrelated_scores_cannot_fill_a_review():
    for records in [
        scores()[:-1],
        scores() + [scores()[0]],
        [dict(s, author_user_id="another") for s in scores()],
        [dict(s, trace_id="another") for s in scores()],
    ]:
        assert check_annotation_completeness(
            target(),
            reviewer_id="human",
            config_ids={n: n for n in CRITERIA},
            scores=records,
        )


def test_pair_decision_requires_both_exact_run_and_output_identities():
    base = target()
    candidate = target(workflow_id="w2", run_id="run2", output_digest="sha256:second")
    from typing import Any

    score: dict[str, Any] = dict(
        scores()[0],
        name="review_decision",
        config_id="decision",
        string_value="accept",
        value=0,
        metadata={
            "comparison": {
                "baseline_run_id": base.run_id,
                "candidate_run_id": candidate.run_id,
                "baseline_output_digest": base.output_digest,
                "candidate_output_digest": candidate.output_digest,
            }
        },
    )
    assert (
        check_pair_decision(
            base, candidate, reviewer_id="human", config_id="decision", score=score
        )
        == ()
    )
    bad_pair = dict(score["metadata"]["comparison"])
    bad_pair["baseline_output_digest"] = "wrong"
    score = dict(score, metadata={"comparison": bad_pair})
    assert check_pair_decision(
        base, candidate, reviewer_id="human", config_id="decision", score=score
    )


def test_pair_decision_rejects_a_conflicting_numeric_category():
    base, candidate = target(), target(workflow_id="w2", run_id="run2")
    record = dict(
        scores()[0],
        name="review_decision",
        config_id="decision",
        string_value="accept",
        value=2,
        metadata={
            "comparison": {
                "baseline_run_id": base.run_id,
                "candidate_run_id": candidate.run_id,
                "baseline_output_digest": base.output_digest,
                "candidate_output_digest": candidate.output_digest,
            }
        },
    )
    assert check_pair_decision(
        base, candidate, reviewer_id="human", config_id="decision", score=record
    )
