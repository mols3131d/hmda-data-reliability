"""Native 사람이 입력한 score의 완비와 대상만 검사한다. 채점하지 않는다."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from hmda_reliability.review_ai.evaluation.identity import (
    CRITERIA,
    ReviewTarget,
    check_comparable_targets,
)


def _owned(score: Mapping[str, Any], target: ReviewTarget, reviewer: str) -> bool:
    return (
        bool(reviewer)
        and score.get("author_user_id") == reviewer
        and score.get("trace_id") == target.trace_id
        and score.get("observation_id") == target.observation_id
    )


def _human(score: Mapping[str, Any], config: str) -> bool:
    timestamp = score.get("timestamp")
    try:
        if (
            not isinstance(timestamp, str)
            or datetime.fromisoformat(timestamp).tzinfo is None
        ):
            return False
    except ValueError:
        return False
    return (
        bool(config)
        and score.get("source") == "ANNOTATION"
        and score.get("config_id") == config
        and score.get("data_type") == "CATEGORICAL"
        and isinstance(score.get("comment"), str)
        and bool(score["comment"].strip())
    )


def check_annotation_completeness(
    target: ReviewTarget,
    *,
    reviewer_id: str,
    config_ids: Mapping[str, str],
    scores: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    errors: list[str] = []
    for criterion in CRITERIA:
        selected = [
            s
            for s in scores
            if _owned(s, target, reviewer_id) and s.get("name") == criterion
        ]
        if len(selected) != 1:
            errors.append("criterion_missing_or_duplicate")
            continue
        score = selected[0]
        label = score.get("string_value")
        value = score.get("value")
        if (
            not _human(score, config_ids.get(criterion, ""))
            or label not in ("0", "1", "2")
            or type(value) not in (int, float)
            or value != int(label)
        ):
            errors.append("invalid_human_score")
    return tuple(sorted(set(errors)))


def check_pair_decision(
    baseline: ReviewTarget,
    candidate: ReviewTarget,
    *,
    reviewer_id: str,
    config_id: str,
    score: Mapping[str, Any],
) -> tuple[str, ...]:
    if error := check_comparable_targets(baseline, candidate):
        return (error,)
    expected = dict(
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        baseline_output_digest=baseline.output_digest,
        candidate_output_digest=candidate.output_digest,
    )
    metadata = score.get("metadata")
    if not isinstance(metadata, Mapping) or metadata.get("comparison") != expected:
        return ("comparison_binding_mismatch",)
    if (
        not _owned(score, candidate, reviewer_id)
        or not _human(score, config_id)
        or score.get("name") != "review_decision"
        or score.get("string_value") not in ("accept", "reject", "no_change")
        or type(score.get("value")) not in (int, float)
        or score.get("value")
        != {"accept": 0, "reject": 1, "no_change": 2}.get(score.get("string_value"))
    ):
        return ("invalid_human_decision",)
    return ()
