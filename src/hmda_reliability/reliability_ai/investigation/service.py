"""도구 기반 단일 에이전트 인시던트 조사 서비스 모듈."""

from __future__ import annotations

import contextlib
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from hmda_reliability.reliability_ai.contracts import AgenticReviewInput
from hmda_reliability.reliability_ai.investigation.contracts import (
    InvestigationFinding,
    InvestigationHypothesis,
    InvestigationResult,
    InvestigationTurnRecord,
    InvestigationUncertainty,
    ToolCallRecord,
)
from hmda_reliability.reliability_ai.investigation.tools import ToolRegistry
from hmda_reliability.reliability_ai.settings import ReliabilityAISettings
from hmda_reliability.reliability_ai.store import InvocationResponseStore
from hmda_reliability.runtime_ai.contracts import (
    ChatMessage,
    ProviderResponse,
)
from hmda_reliability.runtime_ai.provider import (
    OpenAICompatibleAdapter,
    ProviderUnavailableError,
)
from hmda_reliability.runtime_ai.settings import RuntimeAISettings

_SYSTEM_PROMPT = """당신은 HMDA 데이터 신뢰성 인시던트를 조사하는 에이전트입니다.
제공된 정보와 조치 초안을 검토하고, 필요한 경우 도구를 호출해 증거를 확인하세요.
조사가 완료되면 다음 JSON 형식으로 최종 보고서를 반환하세요:
{
  "facts": {"column": "...", "observed_issue": "..."},
  "findings": [{"topic": "...", "description": "...", "evidence_refs": ["..."]}],
  "hypotheses": [
    {"hypothesis": "...", "status": "supported|rejected|uncertain", "rationale": "..."}
  ],
  "uncertainties": [{"topic": "...", "description": "...", "needed_evidence": "..."}]
}
주의:
- 확인되지 않은 사실을 추측으로 단정하지 마세요.
- 도구 호출 결과와 인시던트 데이터에 근거해서만 판단하세요.
- 데이터베이스 변경이나 승인 권한이 없으므로 직접 수정을 시도하지 마세요.
"""


def investigate_incident(
    review_input: AgenticReviewInput,
    *,
    settings: RuntimeAISettings,
    ai_settings: ReliabilityAISettings | None = None,
    provider: OpenAICompatibleAdapter | None = None,
    tool_registry: ToolRegistry | None = None,
    artifact_root: Path = Path(".local/artifacts"),
    clock: Callable[[], float] = time.monotonic,
) -> InvestigationResult:
    """도구 호출을 동적으로 수행하며 인시던트의 원인, 증거, 불확실성을 조사한다."""
    active_ai_settings = ai_settings or ReliabilityAISettings()
    adapter = provider or OpenAICompatibleAdapter(settings, clock=clock)
    registry = tool_registry or ToolRegistry(
        evidence_catalog={e.evidence_id: e for e in review_input.evidence}
    )

    started_at = clock()
    deadline = started_at + active_ai_settings.workflow_budget_seconds
    incident = review_input.incident

    initial_user_message = json.dumps(
        {
            "incident": {
                "incident_id": incident.incident_id,
                "incident_type": incident.incident_type,
                "asset_name": incident.asset_name,
                "partition": incident.partition,
                "severity": incident.severity.value,
                "status": incident.status.value,
                "evidence_refs": incident.evidence_refs,
            },
            "draft_summary": review_input.draft.rca_summary,
            "recommended_actions": review_input.draft.recommended_actions,
        },
        ensure_ascii=False,
    )

    messages: list[ChatMessage] = [
        ChatMessage(role="system", content=_SYSTEM_PROMPT),
        ChatMessage(role="user", content=initial_user_message),
    ]

    all_tool_records: list[ToolCallRecord] = []
    executed_call_fingerprints: set[str] = set()
    turns: list[InvestigationTurnRecord] = []

    store = InvocationResponseStore(artifact_root)

    turn = 0
    max_turns = active_ai_settings.max_tool_calls + 2

    while turn < max_turns:
        remaining_budget = max(0.0, deadline - clock())
        if remaining_budget <= 0:
            return InvestigationResult(
                incident_id=incident.incident_id,
                status="budget_exhausted",
                failure_code="workflow_budget_exhausted",
                tool_calls=tuple(all_tool_records),
            )

        turn_start = clock()
        try:
            response: ProviderResponse = adapter.invoke(
                tuple(messages),
                output_format="text",
                budget_seconds=remaining_budget,
                tools=registry.definitions,
                tool_choice="auto",
            )
        except ProviderUnavailableError as exc:
            return InvestigationResult(
                incident_id=incident.incident_id,
                status="error",
                failure_code=exc.failure_code,
                tool_calls=tuple(all_tool_records),
            )

        turn_latency = max(0.0, (clock() - turn_start) * 1000)

        # 도구 호출이 있는 경우
        if response.tool_calls:
            assistant_msg = ChatMessage(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            messages.append(assistant_msg)
            turns.append(
                InvestigationTurnRecord(
                    turn=turn,
                    role="assistant",
                    content=response.content,
                    tool_calls=tuple(
                        call.model_dump(mode="json") for call in response.tool_calls
                    ),
                    latency_ms=turn_latency,
                )
            )

            cycle_detected = False
            for call in response.tool_calls:
                # 동일 도구 + 동일 인자 반복 호출(cycle) 방어
                fingerprint = f"{call.function.name}:{call.function.arguments.strip()}"
                if fingerprint in executed_call_fingerprints:
                    cycle_detected = True
                    break
                executed_call_fingerprints.add(fingerprint)

                record, tool_output = registry.execute(call)
                all_tool_records.append(record)
                messages.append(
                    ChatMessage(
                        role="tool",
                        tool_call_id=call.id,
                        content=tool_output,
                    )
                )

            if cycle_detected:
                return InvestigationResult(
                    incident_id=incident.incident_id,
                    status="tool_cycle_detected",
                    failure_code="duplicate_tool_call_cycle",
                    tool_calls=tuple(all_tool_records),
                )

            if len(all_tool_records) >= active_ai_settings.max_tool_calls:
                # 도구 호출 한도 도달: 모델에게 최종 보고서 작성을 요청
                messages.append(
                    ChatMessage(
                        role="user",
                        content=(
                            "도구 호출 한도에 도달했습니다. "
                            "현재까지 확인된 정보로 최종 JSON 보고서를 작성하세요."
                        ),
                    )
                )

            turn += 1
            continue

        # 도구 호출이 없는 최종 응답
        turns.append(
            InvestigationTurnRecord(
                turn=turn,
                role="assistant",
                content=response.content,
                latency_ms=turn_latency,
            )
        )

        # 원문 응답 저장소에 보존
        invocation_id = f"inv-{incident.incident_id}-{int(started_at)}"
        with_suppression_store(store, invocation_id, response.content, settings)

        parsed_data = _parse_investigation_payload(response.content)

        return InvestigationResult(
            incident_id=incident.incident_id,
            status="completed",
            facts=parsed_data.get("facts", {}),
            findings=tuple(
                InvestigationFinding.model_validate(f)
                for f in parsed_data.get("findings", [])
            ),
            hypotheses=tuple(
                InvestigationHypothesis.model_validate(h)
                for h in parsed_data.get("hypotheses", [])
            ),
            uncertainties=tuple(
                InvestigationUncertainty.model_validate(u)
                for u in parsed_data.get("uncertainties", [])
            ),
            tool_calls=tuple(all_tool_records),
        )

    return InvestigationResult(
        incident_id=incident.incident_id,
        status="budget_exhausted",
        failure_code="max_turns_exceeded",
        tool_calls=tuple(all_tool_records),
    )


def with_suppression_store(
    store: InvocationResponseStore,
    invocation_id: str,
    content: str,
    settings: RuntimeAISettings,
) -> None:
    with contextlib.suppress(Exception):
        store.write(
            invocation_id,
            content,
            max_response_bytes=settings.max_output_bytes,
        )


def _parse_investigation_payload(content: str) -> dict[str, Any]:
    """JSON 블록을 찾아 파싱하거나 텍스트를 구조화한다."""
    text = content.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {
        "facts": {"raw_summary": content[:500]},
        "findings": [
            {
                "topic": "investigation_summary",
                "description": content[:1000],
                "evidence_refs": [],
            }
        ],
        "hypotheses": [],
        "uncertainties": [
            {
                "topic": "unstructured_output",
                "description": "모델 응답이 JSON 구조가 아니므로 추가 확인 필요",
                "needed_evidence": "정형화된 보고서 재검증",
            }
        ],
    }
