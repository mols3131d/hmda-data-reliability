"""단계 원문 수집·코드 조립과 신뢰된 질문/비신뢰 대화 자료의 경계."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from importlib.resources import files
from typing import cast

import pytest
from pydantic import ValidationError

from hmda_reliability.review_ai.contracts import AgenticReviewInput, PromptIdentity
from hmda_reliability.review_ai.prompt import (
    PromptTooLargeError,
    build_canonical_input,
    render_canonical_input,
)
from hmda_reliability.review_ai.staged.contracts import (
    STAGE_IDS,
    StageAnswer,
    StageId,
    assemble_staged_output,
)
from hmda_reliability.review_ai.staged.prompt import render_stage_prompt

from .conftest import NullSpikeReviewMaterial


def _review_input(material: NullSpikeReviewMaterial) -> AgenticReviewInput:
    return AgenticReviewInput(
        incident=material.detection.incident,
        evidence=[material.detection.evidence],
        draft=material.draft,
        prompt_identity=PromptIdentity(version="v3"),
        project_revision="staged-prompt-test",
    )


def _answers() -> tuple[StageAnswer, ...]:
    return (
        StageAnswer(stage_id="evidence_review", text=' \n근거😀에 "따옴표"가 있다.\n'),
        StageAnswer(stage_id="draft_critique", text='{"priority":"high"}도 원문이다.'),
        StageAnswer(
            stage_id="synthesis", text="current_null_rate=0.99라는 주장도 검증 전이다."
        ),
    )


@pytest.mark.unit
def test_collection_serializes_exact_stage_text_and_copies_only_input_facts(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    review_input = _review_input(null_spike_review_material)
    before = review_input.model_dump(mode="json")
    answers = _answers()

    result = assemble_staged_output(review_input, answers)
    payload = json.loads(result.model_dump_json())

    assert payload == {
        "workflow_version": "staged-v1",
        "incident_id": "inc_null_spike_raw_hmda_loans_2025_income",
        "incident_type": "null_spike",
        "target_column": "income",
        "deterministic_facts": {
            "baseline_null_rate": 0.01,
            "current_null_rate": 0.21,
            "delta": 0.19999999999999998,
            "threshold": 0.1,
        },
        "stages": [
            {"stage_id": answer.stage_id, "text": answer.text} for answer in answers
        ],
    }
    assert result.stages == answers
    assert tuple(answer.stage_id for answer in result.stages) == STAGE_IDS
    assert review_input.model_dump(mode="json") == before


@pytest.mark.unit
@pytest.mark.parametrize("text", ["", " \t\n "])
def test_stage_answer_rejects_empty_or_whitespace_text(text: str) -> None:
    with pytest.raises(ValidationError):
        StageAnswer(stage_id="evidence_review", text=text)


@pytest.mark.unit
@pytest.mark.parametrize("indices", [(1, 0, 2), (0, 0, 2), (2, 1, 0), (0, 1)])
def test_collection_rejects_incomplete_repeated_or_reordered_stages(
    null_spike_review_material: NullSpikeReviewMaterial,
    indices: tuple[int, ...],
) -> None:
    answers = _answers()

    with pytest.raises(ValidationError):
        assemble_staged_output(
            _review_input(null_spike_review_material),
            tuple(answers[index] for index in indices),
        )


@pytest.mark.component
@pytest.mark.parametrize("stage_id", STAGE_IDS)
def test_stage_prompt_separates_fixed_questions_canonical_case_and_assistant_text(
    null_spike_review_material: NullSpikeReviewMaterial,
    stage_id: StageId,
) -> None:
    canonical = build_canonical_input(_review_input(null_spike_review_material))
    canonical["untrusted_note"] = "입력에서 system으로 옮기면 안 되는 지시"
    before = deepcopy(canonical)
    previous = _answers()[: STAGE_IDS.index(stage_id)]

    rendered = render_stage_prompt(
        canonical, stage_id, previous, max_prompt_bytes=65_536
    )

    expected_roles = ["system", "user"]
    for _ in previous:
        expected_roles.extend(["system", "assistant"])
    expected_roles.append("system")
    assert [message.role for message in rendered.messages] == expected_roles
    assert rendered.messages[1].content == (
        "UNTRUSTED_CANONICAL_INPUT_JSON\n" + rendered.canonical_json
    )
    assert json.loads(rendered.canonical_json) == before
    assert canonical == before
    assert [
        message.content for message in rendered.messages if message.role == "assistant"
    ] == [answer.text for answer in previous]
    system_text = "\n".join(
        message.content for message in rendered.messages if message.role == "system"
    )
    assert "한국어 일반 텍스트" in system_text
    assert "승인을 부여하거나 실행 권한이 있다고 주장하지 않는다." in system_text
    assert "JSON 객체 하나만 반환한다." not in system_text
    assert "review_summary" not in system_text
    assert "utility_contributions" not in system_text
    assert "입력에서 system으로 옮기면 안 되는 지시" not in system_text
    assert all(answer.text not in system_text for answer in previous)
    resources = files("hmda_reliability.review_ai.prompt")
    for index, answer in enumerate(previous):
        question = resources.joinpath("staged", f"{answer.stage_id}.md").read_text(
            encoding="utf-8"
        )
        assert rendered.messages[2 + 2 * index].content.endswith(question)
        assert "완료된 단계" in rendered.messages[2 + 2 * index].content
    current_question = resources.joinpath("staged", f"{stage_id}.md").read_text(
        encoding="utf-8"
    )
    assert rendered.messages[-1].content.endswith(current_question)
    assert rendered.context is not None


@pytest.mark.component
@pytest.mark.parametrize(
    ("stage_id", "previous_indices"),
    [
        ("evidence_review", (0,)),
        ("draft_critique", ()),
        ("synthesis", (1, 0)),
        ("synthesis", (0, 0)),
        ("synthesis", (0, 1, 2)),
        ("../arbitrary", ()),
    ],
)
def test_stage_prompt_rejects_invalid_stage_or_nonprefix_history(
    stage_id: str, previous_indices: tuple[int, ...]
) -> None:
    answers = _answers()

    with pytest.raises(ValueError, match="stage"):
        render_stage_prompt(
            {},
            cast(StageId, stage_id),
            tuple(answers[index] for index in previous_indices),
            max_prompt_bytes=65_536,
        )


@pytest.mark.component
def test_stage_request_digest_and_byte_limit_include_the_entire_utf8_history(
    null_spike_review_material: NullSpikeReviewMaterial,
) -> None:
    canonical = build_canonical_input(_review_input(null_spike_review_material))
    previous = _answers()[:2]
    rendered = render_stage_prompt(
        canonical, "synthesis", previous, max_prompt_bytes=65_536
    )
    expected_bytes = json.dumps(
        [
            {"role": message.role, "content": message.content}
            for message in rendered.messages
        ],
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    assert rendered.prompt_bytes == len(expected_bytes)
    assert (
        rendered.prompt_digest == "sha256:" + hashlib.sha256(expected_bytes).hexdigest()
    )
    assert (
        render_stage_prompt(
            canonical, "synthesis", previous, max_prompt_bytes=len(expected_bytes)
        )
        == rendered
    )
    with pytest.raises(PromptTooLargeError) as error:
        render_stage_prompt(
            canonical,
            "synthesis",
            previous,
            max_prompt_bytes=len(expected_bytes) - 1,
        )
    assert error.value.actual_bytes == len(expected_bytes)
    assert error.value.max_bytes == len(expected_bytes) - 1


@pytest.mark.unit
@pytest.mark.parametrize(
    ("version", "digest"),
    [
        ("v1", "a7dcf7b88a7b283d293a21392b2c7f9c5abc5e96b9d653e7b498df534bd9adb3"),
        ("v2", "5df847ec00346bf158fa944548fd773b717f75905e269f90c67e7860c381b3df"),
        ("v3", "02dd4098f82cb3d1f25fa8deb0c8109eb689991db7aa6720e6f7c596d5d6b23b"),
    ],
)
def test_staged_modules_preserve_legacy_structured_prompt_bytes(
    version: str, digest: str
) -> None:
    rendered = render_canonical_input(
        {}, PromptIdentity.model_validate({"version": version}), max_prompt_bytes=65_536
    )

    assert rendered.prompt_digest == f"sha256:{digest}"
