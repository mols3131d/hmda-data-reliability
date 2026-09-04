"""Raw 데이터부터 분석 마트까지의 데이터 플레인을 위한 Airflow 어댑터."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import datetime
from typing import Final

from airflow.sdk import Asset, Param, dag, get_current_context, task
from airflow.sdk.exceptions import AirflowException, AirflowSkipException
from pydantic.types import JsonValue

from hmda_reliability.data_operations import (
    load_raw_data,
    promote_dbt_artifacts,
    run_dbt_build,
)
from hmda_reliability.orchestration.config import data_operation_request_from_runtime
from hmda_reliability.orchestration.quality_gate import (
    QualityGateError,
    evaluate_quality_gate,
)

log = logging.getLogger(__name__)

RAW_HMDA_LOANS_ASSET: Final = Asset("hmda/raw/hmda_loans")
ANALYTICS_LOAN_ASSET: Final = Asset("hmda/analytics/loan_analytics")

_RUNTIME_OVERRIDE_FIELDS: Final = (
    "database_path",
    "source_root",
    "source_year",
    "source_file",
    "run_dbt_build",
)


def _runtime_overrides() -> dict[str, object]:
    """Airflow 트리거 폼에서 제공된 런타임 필드만 읽어온다."""

    context = get_current_context()
    params = context.get("params", {})
    return {
        field: params[field]
        for field in _RUNTIME_OVERRIDE_FIELDS
        if field in params and params[field] is not None
    }


def _set_asset_evidence(asset: Asset, evidence: Mapping[str, JsonValue]) -> None:
    """성공한 아울렛에 실행 독립적 데이터 갱신 evidence를 연결한다."""

    context = get_current_context()
    context["outlet_events"][asset].extra.update(evidence)


@task(
    task_id="load_raw_hmda_loans",
    outlets=[RAW_HMDA_LOANS_ASSET],
    retries=0,
    do_xcom_push=False,
)
def load_raw_hmda_loans() -> None:
    """원천 데이터 수집 및 적재를 Data Operations로 위임한다."""

    request = data_operation_request_from_runtime(_runtime_overrides())
    result = load_raw_data(request)
    _set_asset_evidence(
        RAW_HMDA_LOANS_ASSET,
        {
            "execution_stage": "raw_load",
            "data_update": True,
            "database_path": str(result.database_path),
            "source_root": str(result.source_root),
            "source_file_count": result.source_file_count,
            "source_year": result.source_year,
            "hmda_loans_row_count": result.hmda_loans_row_count,
        },
    )
    log.info(
        "raw HMDA loans 적재 완료: source_year=%s row_count=%s",
        result.source_year,
        result.hmda_loans_row_count,
    )


@task(
    task_id="evaluate_quality_gate",
    retries=0,
    do_xcom_push=False,
)
def evaluate_quality_gate_task() -> None:
    """신뢰성 품질 게이트를 실행하고 이상 탐지 시 파이프라인을 실패시킨다."""

    request = data_operation_request_from_runtime(_runtime_overrides())
    try:
        evaluate_quality_gate(request)
    except QualityGateError as exc:
        raise AirflowException(str(exc)) from exc
    except Exception as exc:
        log.exception("품질 게이트 실행 중 예상치 못한 오류 발생")
        raise AirflowException(
            f"품질 게이트 평가 실패: source_year={request.source_year} "
            f"asset={request.asset_name}: {exc}"
        ) from exc
    log.info(
        "품질 게이트 통과: source_year=%s asset=%s status=clean",
        request.source_year,
        request.asset_name,
    )


@task(
    task_id="build_dbt_loan_analytics",
    outlets=[ANALYTICS_LOAN_ASSET],
    retries=0,
    do_xcom_push=False,
)
def build_dbt_loan_analytics() -> None:
    """dbt build 및 candidate 승격을 Data Operations로 위임한다."""

    request = data_operation_request_from_runtime(_runtime_overrides())
    if not request.run_dbt_build:
        log.info("dbt build 건너뜀: run_dbt_build=false")
        raise AirflowSkipException("run_dbt_build=false")

    result = run_dbt_build(request)
    promote_dbt_artifacts(result, request)
    _set_asset_evidence(
        ANALYTICS_LOAN_ASSET,
        {
            "execution_stage": "analytics_build",
            "data_update": True,
            "return_code": result.return_code,
            "manifest_path": str(result.manifest_path),
            "run_results_path": str(result.run_results_path),
            "projection_id": result.projection_id,
        },
    )
    log.info("dbt loan analytics 완료: projection_id=%s", result.projection_id)


@dag(
    dag_id="hmda_data_plane",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    params={
        "database_path": Param(None, type=["null", "string"]),
        "source_root": Param(None, type=["null", "string"]),
        "source_year": Param(None, type=["null", "integer"]),
        "source_file": Param(None, type=["null", "string"]),
        "run_dbt_build": Param(None, type=["null", "boolean"]),
    },
)
def _hmda_data_plane() -> None:
    """단일 수동 실행, 비재시도 raw-to-analytics 워크플로우를 정의한다."""

    raw_task = load_raw_hmda_loans()
    gate_task = evaluate_quality_gate_task()
    analytics_task = build_dbt_loan_analytics()
    raw_task >> gate_task >> analytics_task


hmda_data_plane = _hmda_data_plane()
