"""같은 사례와 이전 원문을 유지하는 고정 단계의 텍스트 프롬프트."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from importlib.resources import files

from hmda_reliability.review_ai.context import BoundedReviewContext
from hmda_reliability.review_ai.prompt import (
    PromptTooLargeError,
    RenderedReviewPrompt,
    canonical_json_bytes,
)
from hmda_reliability.review_ai.staged.contracts import STAGE_IDS, StageAnswer, StageId
from hmda_reliability.runtime_ai.contracts import ChatMessage

_STAGE_PARTS: dict[StageId, tuple[str, ...]] = {
    "evidence_review": (
        "tasks/null_spike.md",
        "policies/language.md",
        "output/prose.md",
        "guidance/numeric_fidelity.md",
        "guidance/evidence_review.md",
        "policies/advisory.md",
    ),
    "draft_critique": (
        "tasks/null_spike.md",
        "policies/language.md",
        "output/prose.md",
        "guidance/evidence_review.md",
        "policies/advisory.md",
    ),
    "synthesis": (
        "tasks/null_spike.md",
        "policies/language.md",
        "output/prose.md",
        "guidance/numeric_fidelity.md",
        "guidance/evidence_review.md",
        "policies/advisory.md",
    ),
}


def _load_parts(parts: tuple[str, ...]) -> str:
    resources = files("hmda_reliability.review_ai.prompt")
    return "\n".join(
        resources.joinpath(path).read_text(encoding="utf-8") for path in parts
    )


_SYSTEM_INSTRUCTIONS = {
    stage_id: _load_parts(parts) for stage_id, parts in _STAGE_PARTS.items()
}
_STAGE_QUESTIONS = {
    stage_id: _load_parts((f"staged/{stage_id}.md",)) for stage_id in STAGE_IDS
}


def render_stage_prompt(
    canonical_input: dict[str, object],
    stage_id: StageId,
    previous_answers: tuple[StageAnswer, ...],
    *,
    max_prompt_bytes: int,
) -> RenderedReviewPrompt:
    try:
        stage_index = STAGE_IDS.index(stage_id)
    except ValueError:
        msg = "unsupported review stage"
        raise ValueError(msg) from None
    if tuple(answer.stage_id for answer in previous_answers) != STAGE_IDS[:stage_index]:
        msg = "previous stage answers must match the completed stage prefix"
        raise ValueError(msg)

    canonical_snapshot = deepcopy(canonical_input)
    canonical_json = canonical_json_bytes(canonical_snapshot).decode("utf-8")
    messages = [
        ChatMessage(role="system", content=_SYSTEM_INSTRUCTIONS[stage_id]),
        ChatMessage(
            role="user", content=f"UNTRUSTED_CANONICAL_INPUT_JSON\n{canonical_json}"
        ),
    ]
    for answer in previous_answers:
        messages.extend(
            (
                ChatMessage(
                    role="system",
                    content=(
                        "완료된 단계의 고정 질문입니다. "
                        "현재 답변할 질문이 아닙니다.\n\n"
                        + _STAGE_QUESTIONS[answer.stage_id]
                    ),
                ),
                ChatMessage(role="assistant", content=answer.text),
            )
        )
    messages.append(
        ChatMessage(
            role="system",
            content="현재 단계의 고정 질문입니다.\n\n" + _STAGE_QUESTIONS[stage_id],
        )
    )
    rendered_bytes = canonical_json_bytes(
        [message.model_dump(mode="json") for message in messages]
    )
    if len(rendered_bytes) > max_prompt_bytes:
        raise PromptTooLargeError(
            actual_bytes=len(rendered_bytes), max_bytes=max_prompt_bytes
        )
    context_value = canonical_snapshot.get("review_context")
    context = None
    if context_value is not None:
        if not isinstance(context_value, dict):
            msg = "review_context must be an object"
            raise ValueError(msg)
        context = BoundedReviewContext.model_validate(context_value)
    return RenderedReviewPrompt(
        canonical_input=canonical_snapshot,
        canonical_json=canonical_json,
        messages=tuple(messages),
        prompt_digest="sha256:" + hashlib.sha256(rendered_bytes).hexdigest(),
        prompt_bytes=len(rendered_bytes),
        context=context,
    )
