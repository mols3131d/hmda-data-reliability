"""Build deterministic remediation drafts without executing recovery actions."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from hmda_reliability.reliability.errors import RemediationError
from hmda_reliability.reliability.remediation.draft import RemediationDraft
from hmda_reliability.reliability.remediation.request import RemediationDraftRequest


class RemediationState(TypedDict, total=False):
    """Internal state for deterministic triage, RCA, and plan assembly."""

    request: RemediationDraftRequest
    affected_assets: list[str]
    rca_summary: str
    recommended_actions: list[str]
    dbt_test_suggestions: list[str]
    backfill_actions: list[str]
    validation_actions: list[str]
    draft: RemediationDraft


def create_remediation_draft(request: RemediationDraftRequest) -> RemediationDraft:
    """Create a review draft; never approve, backfill, validate, or run dbt."""

    graph = _build_graph()
    final_state = graph.invoke({"request": request})
    draft = final_state.get("draft")
    if not isinstance(draft, RemediationDraft):
        msg = "remediation workflow가 draft를 생성하지 못했습니다."
        raise RemediationError(msg)
    return draft


def _build_graph() -> Any:
    # LangGraph의 TypedDict Protocol은 ty에서 구조적으로 인식되지 않는다.
    graph = StateGraph(RemediationState)  # ty: ignore[invalid-argument-type]
    graph.add_node("triage", _triage_node)
    graph.add_node("rca", _rca_node)
    graph.add_node("plan", _plan_node)
    graph.set_entry_point("triage")
    graph.add_edge("triage", "rca")
    graph.add_edge("rca", "plan")
    graph.add_edge("plan", END)
    return graph.compile()


def _triage_node(state: RemediationState) -> RemediationState:
    request = state["request"]
    if request.lineage_evidence is not None:
        affected_assets = request.lineage_evidence.downstream_assets
    else:
        affected_assets = request.incident.affected_assets
    return {
        **state,
        "affected_assets": affected_assets,
    }


def _rca_node(state: RemediationState) -> RemediationState:
    request = state["request"]
    summary = _rca_summary(
        incident_type=request.incident.incident_type,
        payload=request.evidence.payload,
    )
    return {
        **state,
        "rca_summary": summary,
    }


def _plan_node(state: RemediationState) -> RemediationState:
    request = state["request"]
    incident = request.incident
    recommended_actions = _unique(
        [
            *incident.recommended_actions,
            *_required_actions(incident.incident_type),
        ]
    )
    dbt_test_suggestions = _dbt_test_suggestions(incident.incident_type)
    backfill_actions = _backfill_actions(incident.incident_type)
    validation_actions = _validation_actions(incident.incident_type)
    draft = RemediationDraft(
        incident_id=incident.incident_id,
        incident_type=incident.incident_type,
        asset_name=incident.asset_name,
        partition=incident.partition,
        rca_summary=state["rca_summary"],
        evidence_refs=incident.evidence_refs,
        affected_assets=state["affected_assets"],
        recommended_actions=recommended_actions,
        dbt_test_suggestions=dbt_test_suggestions,
        backfill_actions=backfill_actions,
        validation_actions=validation_actions,
        # A backfill recommendation requires review; this flag never grants approval.
        requires_approval=bool(backfill_actions),
    )
    return {
        **state,
        "recommended_actions": recommended_actions,
        "dbt_test_suggestions": dbt_test_suggestions,
        "backfill_actions": backfill_actions,
        "validation_actions": validation_actions,
        "draft": draft,
    }


def _rca_summary(*, incident_type: str, payload: dict[str, Any]) -> str:
    if incident_type == "volume_drop":
        return (
            "현재 파티션 row_count가 baseline 대비 감소했다. "
            f"drop_ratio={payload.get('drop_ratio')}"
        )
    if incident_type == "null_spike":
        return (
            "핵심 컬럼 null rate가 baseline 대비 증가했다. "
            f"column={payload.get('column')}"
        )
    if incident_type == "schema_drift":
        return (
            "현재 schema hash가 baseline과 달라 downstream 모델 호환성 확인이 필요하다."
        )
    if incident_type == "freshness_delay":
        return (
            "현재 Bronze partition ingestion freshness age가 최대 허용치를 넘었다. "
            f"freshness_age_minutes={payload.get('freshness_age_minutes')}"
        )
    return f"{incident_type} incident에 대한 evidence 검토가 필요하다."


def _required_actions(incident_type: str) -> list[str]:
    return {
        "volume_drop": ["validate_source_partition", "prepare_partition_backfill"],
        "null_spike": ["validate_source_partition", "add_dbt_not_null_test"],
        "schema_drift": ["compare_schema_contract", "validate_dbt_build"],
        "freshness_delay": [
            "check_bronze_ingestion_freshness",
            "prepare_partition_backfill",
        ],
    }.get(incident_type, ["validate_source_partition"])


def _dbt_test_suggestions(incident_type: str) -> list[str]:
    return {
        "volume_drop": ["add_row_count_expectation"],
        "null_spike": ["add_not_null_test_for_spiking_column"],
        "schema_drift": ["add_schema_contract_test"],
        "freshness_delay": ["add_freshness_sla_test"],
    }.get(incident_type, [])


def _backfill_actions(incident_type: str) -> list[str]:
    if incident_type in {"volume_drop", "freshness_delay"}:
        return ["prepare_partition_backfill"]
    return []


def _validation_actions(incident_type: str) -> list[str]:
    base_actions = ["rerun_profile_snapshot", "rerun_dbt_build"]
    if incident_type == "schema_drift":
        return [*base_actions, "validate_schema_hash"]
    if incident_type == "null_spike":
        return [*base_actions, "validate_null_rate"]
    return base_actions


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
