"""Airflow에 의존하지 않는 데이터 품질 게이트 도메인 로직."""

from __future__ import annotations

from datetime import UTC, datetime

from hmda_reliability.data_operations.request import DataOperationRequest
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.logger import get_logger
from hmda_reliability.reliability import (
    ProfileSnapshot,
    ProfileSnapshotRequest,
    create_profile_snapshot,
)
from hmda_reliability.reliability.detection import (
    DetectionRequest,
    DetectionResult,
    DetectionThresholds,
    detect_basic_incidents,
)

_LOGGER = get_logger(__name__)

# 현재 게이트는 null_spike 감지만 활성화한다.
# volume_drop은 baseline row_count 저장소 부재로 ratio=1.0 설정을 통해 비활성화한다.
# schema_drift는 baseline에 current schema_hash를 그대로 복사하여 비활성화한다.
# freshness_delay는 freshness_column=None 전달로 ProfileSnapshot에서
# freshness_status=UNAVAILABLE이 되어 감지기가 자동으로 건너뛴다.
_GATE_THRESHOLDS = DetectionThresholds(
    volume_drop_ratio=1.0,  # row_count != 0이면 ratio < 1.0이므로 비활성화
    null_spike_delta=0.05,  # 5%p 초과 상승 시 탐지
    freshness_max_age_minutes=60.0,
)

# 지원되는 baseline null rate (profile_columns 기본값과 동기화)
_BASELINE_NULL_RATES: dict[str, float] = {
    "income": 0.003,
    "loan_amount": 0.001,
}


class QualityGateError(Exception):
    """신뢰성 이상이 탐지되었을 때 발생하는 품질 게이트 예외."""

    def __init__(self, message: str, detected_incident_types: list[str]) -> None:
        super().__init__(message)
        self.detected_incident_types = detected_incident_types


def evaluate_quality_gate(request: DataOperationRequest) -> None:
    """적재된 파티션의 null_spike를 baseline과 비교해 이상 탐지 시 오류를 발생시킨다.

    파티션에 적재된 행이 0건이거나 신뢰성 이상이 감지되면 QualityGateError를 발생시킨다.
    이상이 없으면 예외 없이 반환한다. Airflow 의존성을 가지지 않는다.
    """

    # profile_columns 중 baseline에 없는 컬럼이 있으면 false positive 위험
    unsupported_columns = set(request.profile_columns) - set(
        _BASELINE_NULL_RATES.keys()
    )
    if unsupported_columns:
        cols = ", ".join(sorted(unsupported_columns))
        msg = f"품질 게이트는 다음 프로파일 컬럼의 baseline을 지원하지 않습니다: {cols}"
        raise ValueError(msg)

    observed_at = request.observed_at or datetime.now(UTC)
    profile_request = ProfileSnapshotRequest(
        asset_name=request.asset_name,
        table_name=request.raw_table_name,
        partition_column=request.partition_column,
        partition=request.source_year,
        profile_columns=request.profile_columns,
        observed_at=observed_at,
    )

    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        current = create_profile_snapshot(connection, profile_request)

    if current.row_count == 0:
        unique_incidents = ["empty_partition"]
        _LOGGER.warning(
            "품질 게이트 실패: 빈 파티션 감지됨",
            extra={
                "source_year": request.source_year,
                "asset_name": request.asset_name,
                "detected_incident_types": unique_incidents,
            },
        )
        msg = (
            f"품질 게이트 실패: source_year={request.source_year} "
            f"asset={request.asset_name} "
            f"detected=[empty_partition] (적재된 행이 0건입니다)"
        )
        raise QualityGateError(msg, unique_incidents)

    baseline = _build_baseline(current)

    detection_request = DetectionRequest(
        baseline=baseline,
        current=current,
        thresholds=_GATE_THRESHOLDS,
    )
    detection_results: list[DetectionResult] = detect_basic_incidents(detection_request)

    # Finding 4: column discriminator를 유지하여 상세 이상 식별자 생성
    incident_details: list[str] = []
    for r in detection_results:
        col = r.evidence.payload.get("column")
        if col:
            incident_details.append(f"{r.incident.incident_type}({col})")
        else:
            incident_details.append(r.incident.incident_type)

    if incident_details:
        # 중복 제거 및 정렬
        unique_incidents = sorted(set(incident_details))
        _LOGGER.warning(
            "품질 게이트 실패: 이상 탐지됨",
            extra={
                "source_year": request.source_year,
                "asset_name": request.asset_name,
                "detected_incident_types": unique_incidents,
            },
        )
        incident_str = ", ".join(unique_incidents)
        msg = (
            f"품질 게이트 실패: source_year={request.source_year} "
            f"asset={request.asset_name} "
            f"detected=[{incident_str}]"
        )
        raise QualityGateError(msg, unique_incidents)

    _LOGGER.info(
        "품질 게이트 통과: 이상 없음",
        extra={
            "source_year": request.source_year,
            "asset_name": request.asset_name,
            "status": "clean",
        },
    )


def _build_baseline(current: ProfileSnapshot) -> ProfileSnapshot:
    """current의 row_count·schema_hash를 그대로 유지하고,
    null_rates만 내장 기준값으로 교체한다."""

    return current.model_copy(update={"null_rates": _BASELINE_NULL_RATES})
