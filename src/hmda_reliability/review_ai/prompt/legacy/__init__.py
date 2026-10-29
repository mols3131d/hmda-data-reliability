"""동결된 v1~v3 structured 프롬프트의 명시적 재생 경로."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from importlib.resources import files

from hmda_reliability.review_ai.context import (
    BoundedReviewContext,
    build_bounded_review_context,
)
from hmda_reliability.review_ai.contracts import AgenticReviewInput, PromptIdentity
from hmda_reliability.review_ai.prompt import (
    PromptTooLargeError,
    RenderedReviewPrompt,
    build_canonical_input,
    canonical_json_bytes,
)
from hmda_reliability.runtime_ai.contracts import ChatMessage

_SYSTEM_INSTRUCTION_V1 = (
    files(__package__).joinpath("v1.md").read_text(encoding="utf-8")
)
_SYSTEM_INSTRUCTION_V2 = (
    files(__package__).joinpath("v2.md").read_text(encoding="utf-8")
)
_SYSTEM_INSTRUCTION_V3 = (
    files(__package__).joinpath("v3.md").read_text(encoding="utf-8")
)


def render_review_prompt(
    review_input: AgenticReviewInput,
    *,
    max_prompt_bytes: int,
) -> RenderedReviewPrompt:
    """불변의 review 입력을 메시지 튜플 및 SHA-256 프롬프트 다이제스트로 투영한다.

    표준 입력 allowlist를 구성하고 system/user 대화 메시지를 포맷팅한다.
    렌더링된 프롬프트 바이트가 `max_prompt_bytes`를 초과하면
    `PromptTooLargeError`를 발생시킨다.
    """

    context = build_bounded_review_context(review_input)
    return render_canonical_input(
        build_canonical_input(review_input, context=context),
        review_input.prompt_identity,
        context=context,
        max_prompt_bytes=max_prompt_bytes,
    )


def render_canonical_input(
    canonical_input: dict[str, object],
    prompt_identity: PromptIdentity,
    *,
    max_prompt_bytes: int,
    context: BoundedReviewContext | None = None,
) -> RenderedReviewPrompt:
    """저장된 표준 입력을 버전이 지정된 프롬프트 템플릿으로 렌더링한다.

    신뢰할 수 없는 JSON 형태의 user 메시지와 고정된 system 지침을 구성하고,
    렌더링된 JSON 바이트에 대해 결정론적 `sha256` 다이제스트를 계산한다.

    렌더링된 메시지가 `max_prompt_bytes`를 초과하면 `PromptTooLargeError`를 발생시킨다.
    """

    instruction = {
        "v1": _SYSTEM_INSTRUCTION_V1,
        "v2": _SYSTEM_INSTRUCTION_V2,
        "v3": _SYSTEM_INSTRUCTION_V3,
    }[prompt_identity.version]
    canonical_snapshot = deepcopy(canonical_input)
    canonical_json = canonical_json_bytes(canonical_snapshot).decode("utf-8")
    messages = (
        ChatMessage(role="system", content=instruction),
        ChatMessage(
            role="user",
            content=(f"UNTRUSTED_CANONICAL_INPUT_JSON\n{canonical_json}"),
        ),
    )
    message_payload = [message.model_dump(mode="json") for message in messages]
    rendered_bytes = canonical_json_bytes(message_payload)
    if len(rendered_bytes) > max_prompt_bytes:
        raise PromptTooLargeError(
            actual_bytes=len(rendered_bytes),
            max_bytes=max_prompt_bytes,
        )
    return RenderedReviewPrompt(
        canonical_input=canonical_snapshot,
        canonical_json=canonical_json,
        messages=messages,
        prompt_digest=f"sha256:{hashlib.sha256(rendered_bytes).hexdigest()}",
        prompt_bytes=len(rendered_bytes),
        context=context or _context_from_canonical_input(canonical_snapshot),
    )


def _context_from_canonical_input(
    canonical_input: dict[str, object],
) -> BoundedReviewContext | None:
    value = canonical_input.get("review_context")
    if value is None:
        return None
    if not isinstance(value, dict):
        msg = "review_context must be an object"
        raise ValueError(msg)
    return BoundedReviewContext.model_validate(value)
