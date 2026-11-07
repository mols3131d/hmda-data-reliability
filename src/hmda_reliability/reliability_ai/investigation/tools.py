"""조사 에이전트를 위한 읽기 전용 도구(Read-only Tools) 및 게이트웨이 모듈."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, StringConstraints

from hmda_reliability.data_platform.artifacts import (
    artifact_projection_id,
    artifact_projection_lock,
)
from hmda_reliability.reliability.assessment.impact import (
    ImpactAnalysisRequest,
    analyze_dbt_impact,
)
from hmda_reliability.reliability.contracts import Evidence, EvidenceSource
from hmda_reliability.reliability_ai.context import (
    project_current_impact,
    project_remote_output,
    project_review_evidence,
)
from hmda_reliability.reliability_ai.contracts import AgenticReviewInput
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


class _ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class _EvidenceArguments(_ToolArguments):
    evidence_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _ProfileArguments(_ToolArguments):
    column: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None
    ) = None


class _ImpactArguments(_ToolArguments):
    asset_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ToolRegistry:
    """조사 에이전트가 호출할 수 있는 안전한 읽기 전용 도구들의 디스패처."""

    def __init__(
        self,
        *,
        evidence_catalog: dict[str, Evidence] | None = None,
        profile_comparison_handler: Callable[[dict[str, Any]], dict[str, Any]]
        | None = None,
        impact_handler: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
        allowed_tools: tuple[str, ...] | None = None,
    ) -> None:
        self._evidence_catalog = dict(evidence_catalog or {})
        self._profile_comparison_handler = profile_comparison_handler
        self._impact_handler = impact_handler
        available = [GET_INCIDENT_EVIDENCE_TOOL]
        if profile_comparison_handler is not None:
            available.append(COMPARE_PROFILES_TOOL)
        if impact_handler is not None:
            available.append(INSPECT_DBT_IMPACT_TOOL)
        self._definitions = tuple(
            definition
            for definition in available
            if allowed_tools is None or definition.function.name in allowed_tools
        )

    @classmethod
    def from_review_input(
        cls,
        review_input: AgenticReviewInput,
        *,
        allowed_tools: tuple[str, ...] | None = None,
        dbt_artifact_paths: tuple[Path, Path] | None = None,
    ) -> ToolRegistry:
        """사건의 불변 profile evidence만 비교하며 live 상태로 대체하지 않는다."""
        snapshot = AgenticReviewInput.model_validate(review_input.model_dump())
        target = next(
            evidence
            for evidence in snapshot.evidence
            if evidence.source is EvidenceSource.PROFILE
            and evidence.payload.get("rule") == "null_spike"
            and evidence.asset_name == snapshot.incident.asset_name
            and evidence.partition == snapshot.incident.partition
        )

        def compare_profiles(arguments: dict[str, Any]) -> dict[str, Any]:
            column = arguments.get("column", snapshot.target_column)
            if column != snapshot.target_column:
                raise ValueError("column is outside the incident evidence scope")
            snapshot_refs: dict[str, object] = {}
            for key in (
                "snapshot_id",
                "baseline_snapshot_id",
                "current_snapshot_id",
            ):
                reference = target.payload.get(key)
                if isinstance(reference, str):
                    if len(reference.encode("utf-8")) > 1024:
                        raise ValueError(
                            "snapshot reference exceeds the projection limit"
                        )
                    snapshot_refs[key] = reference
            return {
                "asset_name": target.asset_name,
                "partition": target.partition,
                "column": snapshot.target_column,
                **snapshot.deterministic_facts.model_dump(mode="json"),
                "provenance": {
                    "kind": "incident_snapshot",
                    "evidence_id": target.evidence_id,
                    "source": target.source.value,
                    "observed_at": target.observed_at.isoformat(),
                    **project_remote_output(snapshot_refs),
                },
            }

        impact_handler = None
        if dbt_artifact_paths is not None:
            manifest_path, run_results_path = (
                path.resolve() for path in dbt_artifact_paths
            )

            def inspect_dbt_impact(arguments: dict[str, Any]) -> dict[str, Any]:
                if arguments["asset_name"] != snapshot.incident.asset_name:
                    raise ValueError("asset is outside the incident evidence scope")
                if manifest_path.parent != run_results_path.parent:
                    raise ValueError(
                        "dbt artifact pair must share a projection directory"
                    )
                with artifact_projection_lock(manifest_path.parent, exclusive=False):
                    projection_id = artifact_projection_id(
                        manifest_path, run_results_path
                    )
                    result = analyze_dbt_impact(
                        ImpactAnalysisRequest(
                            incident=snapshot.incident,
                            dbt_manifest_path=manifest_path,
                            dbt_run_results_path=run_results_path,
                        )
                    )
                return {
                    "asset_name": snapshot.incident.asset_name,
                    "partition": snapshot.incident.partition,
                    **project_current_impact(
                        result.lineage_evidence,
                        projection_id=projection_id,
                        observed_at=datetime.now(UTC),
                    ),
                }

            impact_handler = inspect_dbt_impact

        return cls(
            evidence_catalog={item.evidence_id: item for item in snapshot.evidence},
            profile_comparison_handler=compare_profiles,
            impact_handler=impact_handler,
            allowed_tools=allowed_tools,
        )

    @property
    def definitions(self) -> tuple[ToolDefinition, ...]:
        return self._definitions

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
        except (ValueError, RecursionError):
            latency_ms = max(0.0, (time.monotonic() - started) * 1000)
            err_result = {"error": "invalid_arguments"}
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
            if tool_name not in {tool.function.name for tool in self.definitions}:
                result = {"error": "unknown tool or unavailable capability"}
                status = "error"
            else:
                result = project_remote_output(self._dispatch(tool_name, arguments))
                status = "success"
        except Exception as exc:
            result = {
                "error": "tool_execution_failed",
                "error_type": type(exc).__name__,
            }
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
        if tool_name not in {tool.function.name for tool in self.definitions}:
            raise ValueError(f"unknown tool or unavailable capability: {tool_name}")

        if tool_name == "get_incident_evidence":
            evidence_id = _EvidenceArguments.model_validate(arguments).evidence_id
            if evidence_id not in self._evidence_catalog:
                return {
                    "found": False,
                    "evidence_id": evidence_id,
                    "message": "해당 ID의 증거를 찾을 수 없습니다.",
                }
            evidence = project_review_evidence(self._evidence_catalog[evidence_id])
            return {
                "found": True,
                "evidence_id": evidence.evidence_id,
                "source": evidence.source.value,
                "asset_name": evidence.provenance.asset_name,
                "partition": evidence.provenance.partition,
                "observed_at": evidence.provenance.observed_at.isoformat(),
                "summary": evidence.summary,
                "payload": evidence.facts,
            }

        if tool_name == "compare_profiles":
            validated = _ProfileArguments.model_validate(arguments)
            if self._profile_comparison_handler is not None:
                return self._profile_comparison_handler(
                    validated.model_dump(exclude_none=True)
                )

        if tool_name == "inspect_dbt_impact":
            validated_impact = _ImpactArguments.model_validate(arguments)
            if self._impact_handler is not None:
                return self._impact_handler(validated_impact.model_dump())

        raise ValueError(f"unknown tool: {tool_name}")
