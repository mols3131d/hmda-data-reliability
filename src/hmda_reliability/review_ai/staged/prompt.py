"""Langfuse chat prompt를 compile하고 실제 이전 원문을 전달한다."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from copy import deepcopy

from langfuse import Langfuse, get_client
from langfuse.model import ChatPromptClient

from hmda_reliability.review_ai.context import BoundedReviewContext
from hmda_reliability.review_ai.prompt import (
    PromptTooLargeError,
    RenderedReviewPrompt,
    canonical_json_bytes,
)
from hmda_reliability.review_ai.staged.contracts import STAGE_IDS, StageAnswer, StageId
from hmda_reliability.runtime_ai.contracts import ChatMessage


def load_stage_prompts(
    *, client: Langfuse | None = None, label: str = "production"
) -> dict[StageId, ChatPromptClient]:
    """한 workflow에서 사용할 native version 객체를 시작 시 고정한다."""
    langfuse = client if client is not None else get_client()
    return {
        stage: langfuse.get_prompt(f"hmda-review-ai/{stage}", type="chat", label=label)
        for stage in STAGE_IDS
    }


def render_stage_prompt(
    canonical_input: dict[str, object],
    stage_id: StageId,
    previous_answers: tuple[StageAnswer, ...],
    *,
    max_prompt_bytes: int,
    prompts: Mapping[StageId, ChatPromptClient] | None = None,
) -> RenderedReviewPrompt:
    try:
        stage_index = STAGE_IDS.index(stage_id)
    except ValueError:
        raise ValueError("unsupported review stage") from None
    if tuple(answer.stage_id for answer in previous_answers) != STAGE_IDS[:stage_index]:
        raise ValueError("previous stage answers must match the completed stage prefix")
    active = load_stage_prompts() if prompts is None else prompts
    prompt = active[stage_id]
    canonical_snapshot = deepcopy(canonical_input)
    canonical_json = canonical_json_bytes(canonical_snapshot).decode("utf-8")
    history = [
        {"role": "user", "content": f"UNTRUSTED_CANONICAL_INPUT_JSON\n{canonical_json}"}
    ]
    for answer in previous_answers:
        question = active[answer.stage_id].prompt[-1].get("content")
        if not isinstance(question, str):
            raise ValueError("previous prompt requires a system question")
        history.extend(
            [
                {
                    "role": "system",
                    "content": question,
                },
                {"role": "assistant", "content": answer.text},
            ]
        )
    placeholders = [
        index
        for index, message in enumerate(prompt.prompt)
        if message.get("type") == "placeholder" and message.get("name") == "history"
    ]
    if (
        not prompt.prompt
        or len(placeholders) != 1
        or prompt.prompt[-1].get("role") != "system"
    ):
        raise ValueError(
            "chat prompt requires one history placeholder and a final system question"
        )
    messages = list(prompt.compile(history=history))
    # SDK 4.15.6은 placeholder 본문도 치환한다. 모델 원문 '{{history}}'까지
    # 바뀌지 않도록 native가 삽입한 구간만 원래 메시지로 보존한다.
    offset = placeholders[0]
    messages[offset : offset + len(history)] = history
    validated = tuple(ChatMessage.model_validate(message) for message in messages)
    rendered_bytes = canonical_json_bytes(
        [message.model_dump(mode="json") for message in validated]
    )
    if len(rendered_bytes) > max_prompt_bytes:
        raise PromptTooLargeError(
            actual_bytes=len(rendered_bytes), max_bytes=max_prompt_bytes
        )
    context_value = canonical_snapshot.get("review_context")
    context = (
        BoundedReviewContext.model_validate(context_value)
        if context_value is not None
        else None
    )
    return RenderedReviewPrompt(
        canonical_input=canonical_snapshot,
        canonical_json=canonical_json,
        messages=validated,
        prompt_digest="sha256:" + hashlib.sha256(rendered_bytes).hexdigest(),
        prompt_bytes=len(rendered_bytes),
        context=context,
    )
