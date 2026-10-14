"""검증된 Review AI 호출 결과를 선택적으로 Langfuse에 사후 투영한다.

상위 프로세스는 호출 기록과 새로 만든 합성 입력을 대조한 뒤 크기가 제한된 자료를
전달한다. SDK는 별도 자식 프로세스에서만 실행한다. 반환 상태는 원격 저장 여부를
확인해 주지 않는다.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import urlsplit

from pydantic import ValidationError

from hmda_reliability.review_ai.contracts import (
    AgenticReviewOutput,
    AgenticReviewStatus,
)
from hmda_reliability.review_ai.evaluation import (
    RUBRIC_V1,
    RubricCriterion,
    RubricScore,
    review_output_digest,
)
from hmda_reliability.review_ai.evidence import AgenticInvocationEvidence

_MAX_BYTES = 65_536
_TRUE_VALUES = {"1", "true", "yes", "on"}


def _encode(payload: Mapping[str, object]) -> str:
    """크기 제한을 적용해 재현 가능한 JSON 문자열을 만든다."""
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if len(encoded.encode("utf-8")) > _MAX_BYTES:
        raise ValueError("projection exceeds byte limit")
    return encoded


def project_invocation(
    record: AgenticInvocationEvidence, *, expected_input: dict[str, object]
) -> dict[str, Any]:
    """검증된 호출 기록을 실행기가 새로 만든 합성 입력과 대조해 투영한다.

    실행기가 출처 검증과 시험 자료를 만든다. `expected_input`은 호출 기록 자체에서
    가져오면 안 된다. `accepted` 결과만 입력과 출력을 포함하고, 나머지는 최소한의
    메타데이터만 내보낸다. 입력이 다르거나 투영할 수 없는 상태면 `ValueError`를
    발생시킨다.
    """
    metadata: dict[str, object] = {
        "invocation_id": record.invocation_id,
        "project_revision": record.project_revision,
        "status": record.status.value,
    }
    payload: dict[str, Any] = {"metadata": metadata}
    if _encode(record.canonical_input) != _encode(expected_input):
        raise ValueError("record does not match synthetic input")
    if record.status is AgenticReviewStatus.ACCEPTED:
        if record.parsed_output is None or record.validation is None:
            raise ValueError("accepted record missing output or validation")
        config = record.configuration
        metadata.update(
            {
                "prompt_template": record.prompt_identity.template_id,
                "prompt_version": record.prompt_identity.version,
                "prompt_digest": record.prompt_digest,
                "rubric_id": RUBRIC_V1.rubric_id,
                "output_digest": review_output_digest(record.parsed_output),
                "validation_policy": record.validation.policy_id,
                "validation_status": record.validation.status.value,
                "model": config.model,
                "timeout_seconds": config.timeout_seconds,
                "max_retries": config.max_retries,
                "temperature": config.temperature,
                "max_output_tokens": config.max_output_tokens,
                "max_prompt_bytes": config.max_prompt_bytes,
                "max_output_bytes": config.max_output_bytes,
                "recorded_at": record.recorded_at.isoformat(),
                "recorded_latency_ms": record.latency_ms,
                "attempt_count": record.attempt_count,
            }
        )
        if record.usage is not None:
            metadata["usage"] = {
                "prompt_tokens": record.usage.prompt_tokens,
                "completion_tokens": record.usage.completion_tokens,
                "total_tokens": record.usage.total_tokens,
            }
        # 합성 입력 전체를 비교해 중첩 항목까지 확인한 뒤 필요한 값만 복사한다.
        payload["input"] = {
            key: expected_input[key]
            for key in (
                "incident",
                "deterministic_facts",
                "draft",
                "evidence",
                "review_context",
            )
        }
        payload["output"] = record.parsed_output.model_dump(
            mode="json",
            include={
                "incident_id",
                "incident_type",
                "target_column",
                "deterministic_facts",
                "review_summary",
                "evidence_used",
                "findings",
                "uncertainties",
                "utility_contributions",
                "advisory_recommendation",
            },
        )
    elif record.status not in {
        AgenticReviewStatus.UNAVAILABLE,
        AgenticReviewStatus.VALIDATION_FAILED,
    }:
        raise ValueError("record is not eligible for projection")
    _encode(payload)
    return payload


def annotation_complete(
    payload: Mapping[str, Any],
    *,
    target: Mapping[str, object],
    scores: Sequence[Mapping[str, object]],
) -> bool:
    """수동 주석 스냅샷의 구조와 대상 연결을 확인한다.

    `accepted` 결과의 정규화 형태와 해시, 대상 식별 정보, 평가 항목 다섯 개의
    점수가 각각 한 번씩 있는지 확인한다. 작성자, 진정성, 평가 품질은 증명하지 않는다.
    """
    metadata = payload.get("metadata")
    if (
        not isinstance(metadata, Mapping)
        or not isinstance(target, Mapping)
        or metadata.get("status") != "accepted"
        or metadata.get("rubric_id") != RUBRIC_V1.rubric_id
    ):
        return False
    raw_output = payload.get("output")
    if not isinstance(raw_output, Mapping):
        return False
    try:
        output = AgenticReviewOutput.model_validate(raw_output)
        if _encode(raw_output) != _encode(output.model_dump(mode="json")):
            return False
    except (TypeError, ValueError):
        return False
    if metadata.get("output_digest") != review_output_digest(output):
        return False
    target_keys = ("invocation_id", "output_digest", "rubric_id")
    if any(
        not isinstance(metadata.get(key), str)
        or not metadata[key]
        or target.get(key) != metadata[key]
        for key in target_keys
    ):
        return False
    if (
        not isinstance(scores, Sequence)
        or isinstance(scores, (str, bytes))
        or len(scores) != len(RubricCriterion)
        or any(
            not isinstance(item, Mapping) or type(item.get("score")) is not int
            for item in scores
        )
    ):
        return False
    try:
        validated = [RubricScore.model_validate(item) for item in scores]
    except ValidationError:
        return False
    return {item.criterion for item in validated} == set(RubricCriterion)


def export_projection(payload: Mapping[str, object], *, env: Mapping[str, str]) -> str:
    """SDK 실행을 제한하고 선택적 전송 상태를 반환한다.

    반환값은 `disabled`, `invalid_config`, `timeout`, `export_failed`,
    `submitted_unverified` 중 하나다. 마지막 상태는 자식 프로세스가 오류 없이
    끝났다는 뜻일 뿐, 원격 저장을 확인하지 않는다. 검토 결과에도 영향을 주지 않는다.
    """
    if env.get("HMDA_LANGFUSE_EXPORT", "").strip().lower() not in _TRUE_VALUES:
        return "disabled"
    try:
        timeout = float(env.get("HMDA_LANGFUSE_TIMEOUT_SECONDS", "5"))
        if not math.isfinite(timeout) or not 0 < timeout <= 60:
            return "invalid_config"
        required = ("LANGFUSE_BASE_URL", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")
        if any(not env.get(key, "").strip() for key in required):
            return "invalid_config"
        url = urlsplit(env["LANGFUSE_BASE_URL"])
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            return "invalid_config"
        encoded = _encode(payload)
    except (ValueError, TypeError):
        return "invalid_config"
    child_env = {key: env[key] for key in required}
    # 자식 실행에 필요한 변수만 전달하고 OpenTelemetry 관련 환경 변수는 제외한다.
    child_env.update(
        {
            key: os.environ[key]
            for key in ("PATH", "SYSTEMROOT", "WINDIR")
            if key in os.environ
        }
    )
    # SDK가 data URI를 미디어로 바꿔 올리지 않도록 문자열로 유지한다.
    child_env["LANGFUSE_MEDIA_UPLOAD_ENABLED"] = "false"
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "hmda_reliability.review_ai.evaluation.langfuse",
            ],
            input=encoded,
            text=True,
            env=child_env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "timeout"
    except OSError:
        return "export_failed"
    return "submitted_unverified" if result.returncode == 0 else "export_failed"


def _send_to_langfuse(payload: dict[str, Any]) -> None:
    """자식 프로세스에서 관측 항목 하나를 전송하고 `flush()`를 호출한다."""
    # 선택적 SDK와 제공자는 부모 프로세스의 Review AI 경로에서 불러오지 않는다.
    from importlib import import_module

    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider

    provider = TracerProvider(
        resource=Resource({"service.name": "hmda-review-projection"})
    )
    client = import_module("langfuse").Langfuse(
        public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
        secret_key=os.environ["LANGFUSE_SECRET_KEY"],
        base_url=os.environ["LANGFUSE_BASE_URL"],
        timeout=2,
        tracer_provider=provider,
        sample_rate=1.0,
    )
    try:
        trace_id = hashlib.sha256(_encode(payload).encode("utf-8")).hexdigest()[:32]
        observation = client.start_observation(
            name="review-ai-post-hoc-projection",
            as_type="span",
            trace_context={"trace_id": trace_id},
            input=payload.get("input"),
            output=payload.get("output"),
            metadata=payload["metadata"],
        )
        observation.end()
        client.flush()
    finally:
        client.shutdown()
        provider.shutdown()


if __name__ == "__main__":
    # 부모가 SDK 출력을 버리고 자식 종료 처리까지 제한 시간으로 통제한다.
    try:
        _send_to_langfuse(json.loads(sys.stdin.buffer.read(_MAX_BYTES + 1)))
    except Exception:
        raise SystemExit(1) from None
