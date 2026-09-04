"""프로파일 기반 데이터 품질 게이트 정책."""

from __future__ import annotations

from typing import Never

from hmda_reliability.logger import get_logger
from hmda_reliability.reliability.contracts import ProfileSnapshot
from hmda_reliability.reliability.detection import (
    DetectionRequest,
    DetectionThresholds,
    detect_basic_incidents,
)
from hmda_reliability.reliability.errors import ReliabilityError

_LOGGER = get_logger(__name__)

_GATE_THRESHOLDS = DetectionThresholds(
    volume_drop_ratio=1.0,
    null_spike_delta=0.05,
    freshness_max_age_minutes=60.0,
)

_BASELINE_NULL_RATES: dict[str, float] = {
    "income": 0.16168766279822375,
    "loan_amount": 0.0,
}
_BLOCKING_INCIDENT_TYPES = frozenset({"null_spike"})


class QualityGateError(ReliabilityError):
    """Blocking 품질 이상이 감지되었을 때 발생하는 예외."""

    def __init__(self, message: str, detected_incident_types: list[str]) -> None:
        super().__init__(message)
        self.detected_incident_types = detected_incident_types


def reject_missing_partition_discriminator(
    *,
    asset_name: str,
    row_count: int,
) -> Never:
    """Partition discriminator가 없는 Bronze population을 차단한다."""

    detected_incidents = ["missing_partition_discriminator"]
    _LOGGER.warning(
        "품질 게이트 실패: 파티션 식별자 누락",
        extra={
            "source_year": None,
            "asset_name": asset_name,
            "detected_incident_types": detected_incidents,
            "row_count": row_count,
        },
    )
    message = (
        f"품질 게이트 실패: asset={asset_name} "
        f"detected=[missing_partition_discriminator] row_count={row_count}"
    )
    raise QualityGateError(message, detected_incidents)


def evaluate_profile_quality_gate(current: ProfileSnapshot) -> None:
    """현재 프로파일을 MVP baseline과 비교해 blocking 이상을 거부한다.

    현재 MVP는 null spike와 빈 파티션만 blocking하며, 지원하지 않는 profile
    column은 baseline 누락으로 인한 false positive를 막기 위해 거부한다.
    """

    current_columns = set(current.null_rates)
    required_columns = set(_BASELINE_NULL_RATES)
    missing_columns = required_columns - current_columns
    if missing_columns:
        columns = ", ".join(sorted(missing_columns))
        _log_profile_coverage_failure(current, "missing_profile_columns")
        message = f"품질 게이트 필수 프로파일 컬럼이 누락되었습니다: {columns}"
        raise ValueError(message)

    unsupported_columns = current_columns - required_columns
    if unsupported_columns:
        columns = ", ".join(sorted(unsupported_columns))
        _log_profile_coverage_failure(current, "unsupported_profile_columns")
        message = (
            "품질 게이트는 다음 프로파일 컬럼의 baseline을 지원하지 않습니다: "
            f"{columns}"
        )
        raise ValueError(message)

    if current.row_count == 0:
        detected_incidents = ["empty_partition"]
        _LOGGER.warning(
            "품질 게이트 실패: 빈 파티션 감지됨",
            extra={
                "source_year": current.partition,
                "asset_name": current.asset_name,
                "detected_incident_types": detected_incidents,
            },
        )
        message = (
            f"품질 게이트 실패: source_year={current.partition} "
            f"asset={current.asset_name} "
            "detected=[empty_partition] (적재된 행이 0건입니다)"
        )
        raise QualityGateError(message, detected_incidents)

    baseline = current.model_copy(update={"null_rates": _BASELINE_NULL_RATES})
    detection_results = detect_basic_incidents(
        DetectionRequest(
            baseline=baseline,
            current=current,
            thresholds=_GATE_THRESHOLDS,
        )
    )
    incident_details = [
        _incident_detail(result.incident.incident_type, result.evidence.payload)
        for result in detection_results
        if result.incident.incident_type in _BLOCKING_INCIDENT_TYPES
    ]

    if incident_details:
        detected_incidents = sorted(set(incident_details))
        _LOGGER.warning(
            "품질 게이트 실패: 이상 탐지됨",
            extra={
                "source_year": current.partition,
                "asset_name": current.asset_name,
                "detected_incident_types": detected_incidents,
            },
        )
        incident_text = ", ".join(detected_incidents)
        message = (
            f"품질 게이트 실패: source_year={current.partition} "
            f"asset={current.asset_name} detected=[{incident_text}]"
        )
        raise QualityGateError(message, detected_incidents)

    _LOGGER.info(
        "품질 게이트 통과: 이상 없음",
        extra={
            "source_year": current.partition,
            "asset_name": current.asset_name,
            "status": "clean",
        },
    )


def _incident_detail(incident_type: str, payload: dict[str, object]) -> str:
    column = payload.get("column")
    if column:
        return f"{incident_type}({column})"
    return incident_type


def _log_profile_coverage_failure(
    current: ProfileSnapshot,
    failure_type: str,
) -> None:
    _LOGGER.warning(
        "품질 게이트 실패: 프로파일 컬럼 계약 불일치",
        extra={
            "source_year": current.partition,
            "asset_name": current.asset_name,
            "detected_incident_types": [failure_type],
        },
    )
