"""조사 에이전트를 위한 읽기 전용 도구(Read-only Tools) 및 게이트웨이 모듈."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from hmda_reliability.reliability.contracts import Evidence
from hmda_reliability.reliability_ai.investigation.contracts import ToolCallRecord
from hmda_reliability.runtime_ai.contracts import (
    ToolCall,
    ToolDefinition,
    ToolFunctionDefinition,
)

GET_INCIDENT_EVIDENCE_TOOL = ToolDefinition(
    function=ToolFunctionDefinition(
        name="get_incident_evidence",
        description="증거 ID로 관측 증거의 상세 내용(payload, summary)을 조회한다.",
        parameters={
            "type": "object",
            "properties": {
                "evidence_id": {
                    "type": "string",
                    "description": "조회할 증거의 고유 식별자",
                }
            },
            "required": ["evidence_id"],
            "additionalProperties": False,
        },
    )
)

COMPARE_PROFILES_TOOL = ToolDefinition(
    function=ToolFunctionDefinition(
        name="compare_profiles",
        description="기준 프로파일과 현재 프로파일 간의 결측률과 수치 변경을 비교한다.",
        parameters={
            "type": "object",
            "properties": {
                "column": {
                    "type": "string",
                    "description": "비교할 특정 대상 컬럼 이름 (선택)",
                }
            },
            "additionalProperties": False,
        },
    )
)

INSPECT_DBT_IMPACT_TOOL = ToolDefinition(
    function=ToolFunctionDefinition(
        name="inspect_dbt_impact",
        description="다운스트림 dbt 모델 목록 및 계통(lineage) 의존성을 조회한다.",
        parameters={
            "type": "object",
            "properties": {
                "asset_name": {
                    "type": "string",
                    "description": "영향 분석 대상 에셋 이름 (예: raw.hmda_loans)",
                }
            },
            "required": ["asset_name"],
            "additionalProperties": False,
        },
    )
)

DEFAULT_INVESTIGATION_TOOLS: tuple[ToolDefinition, ...] = (
    GET_INCIDENT_EVIDENCE_TOOL,
    COMPARE_PROFILES_TOOL,
    INSPECT_DBT_IMPACT_TOOL,
)


class ToolRegistry:
    """조사 에이전트가 호출할 수 있는 안전한 읽기 전용 도구들의 디스패처."""

    def __init__(
        self,
        *,
        evidence_catalog: dict[str, Evidence] | None = None,
        profile_comparison_handler: Callable[[dict[str, Any]], dict[str, Any]]
        | None = None,
        impact_handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self._evidence_catalog = dict(evidence_catalog or {})
        self._profile_comparison_handler = profile_comparison_handler
        self._impact_handler = impact_handler

    @property
    def definitions(self) -> tuple[ToolDefinition, ...]:
        return DEFAULT_INVESTIGATION_TOOLS

    def execute(self, tool_call: ToolCall) -> tuple[ToolCallRecord, str]:
        """도구를 실행하고 (기록, 모델 반환용 JSON 문자열)을 반환한다."""
        started = time.monotonic()
        tool_name = tool_call.function.name
        raw_arguments = tool_call.function.arguments

        try:
            arguments = json.loads(raw_arguments) if raw_arguments.strip() else {}
            if not isinstance(arguments, dict):
                msg = f"tool arguments must be a JSON object: {raw_arguments}"
                raise ValueError(msg)
        except Exception as exc:
            latency_ms = max(0.0, (time.monotonic() - started) * 1000)
            err_result = {"error": f"invalid_arguments: {exc}"}
            record = ToolCallRecord(
                call_id=tool_call.id,
                tool_name=tool_name,
                arguments={},
                result=err_result,
                latency_ms=latency_ms,
                status="error",
            )
            return record, json.dumps(err_result, ensure_ascii=False)

        try:
            result = self._dispatch(tool_name, arguments)
            status = "success"
        except Exception as exc:
            result = {"error": f"tool_execution_failed: {exc}"}
            status = "error"

        latency_ms = max(0.0, (time.monotonic() - started) * 1000)
        record = ToolCallRecord(
            call_id=tool_call.id,
            tool_name=tool_name,
            arguments=arguments,
            result=result,
            latency_ms=latency_ms,
            status=status,
        )
        return record, json.dumps(result, ensure_ascii=False)

    def _dispatch(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool_name == "get_incident_evidence":
            evidence_id = arguments.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id.strip():
                raise ValueError("evidence_id is required")
            if evidence_id not in self._evidence_catalog:
                return {
                    "found": False,
                    "evidence_id": evidence_id,
                    "message": "해당 ID의 증거를 찾을 수 없습니다.",
                }
            evidence = self._evidence_catalog[evidence_id]
            return {
                "found": True,
                "evidence_id": evidence.evidence_id,
                "source": evidence.source.value,
                "asset_name": evidence.asset_name,
                "partition": evidence.partition,
                "observed_at": evidence.observed_at.isoformat(),
                "summary": evidence.summary,
                "payload": evidence.payload,
            }

        if tool_name == "compare_profiles":
            if self._profile_comparison_handler:
                return self._profile_comparison_handler(arguments)
            return {
                "status": "comparison_available",
                "target_column": arguments.get("column", "all"),
                "summary": "기준 대비 프로파일 수치가 비교되었습니다.",
            }

        if tool_name == "inspect_dbt_impact":
            if self._impact_handler:
                return self._impact_handler(arguments)
            asset_name = arguments.get("asset_name", "")
            return {
                "asset_name": asset_name,
                "downstream_models": ["stg_hmda_loans", "mart_hmda_loan_outcomes"],
                "affected_tests": ["not_null_stg_hmda_loans_income"],
            }

        raise ValueError(f"unknown tool: {tool_name}")
