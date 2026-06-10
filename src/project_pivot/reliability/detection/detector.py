"""ProfileSnapshot 비교 기반 기본 incident detector."""

from __future__ import annotations

from datetime import timedelta

from project_pivot.reliability.contracts import (
    Evidence,
    EvidenceSource,
    Incident,
    IncidentSeverity,
    IncidentStatus,
    ProfileSnapshot,
)
from project_pivot.reliability.detection.request import DetectionRequest
from project_pivot.reliability.detection.result import DetectionResult


class BasicIncidentDetector:
    """baseline/current profile을 비교해 기본 incident를 생성한다."""

    def detect(self, request: DetectionRequest) -> list[DetectionResult]:
        """matching rule별 DetectionResult를 반환한다."""

        results: list[DetectionResult] = []
        results.extend(self._detect_volume_drop(request))
        results.extend(self._detect_null_spike(request))
        results.extend(self._detect_schema_drift(request))
        results.extend(self._detect_freshness_delay(request))
        return results

    def _detect_volume_drop(
        self,
        request: DetectionRequest,
    ) -> list[DetectionResult]:
        baseline = request.baseline
        current = request.current
        if baseline.row_count == 0:
            return []
        drop_ratio = (baseline.row_count - current.row_count) / baseline.row_count
        if drop_ratio < request.thresholds.volume_drop_ratio:
            return []
        payload: dict[str, object] = {
            "baseline_row_count": baseline.row_count,
            "current_row_count": current.row_count,
            "drop_ratio": drop_ratio,
            "threshold": request.thresholds.volume_drop_ratio,
        }
        return [
            _result(
                request=request,
                incident_type="volume_drop",
                severity=IncidentSeverity.HIGH,
                summary="row_count가 baseline 대비 급감했다.",
                payload=payload,
            )
        ]

    def _detect_null_spike(
        self,
        request: DetectionRequest,
    ) -> list[DetectionResult]:
        results: list[DetectionResult] = []
        for column, current_rate in sorted(request.current.null_rates.items()):
            baseline_rate = request.baseline.null_rates.get(column, 0.0)
            delta = current_rate - baseline_rate
            if delta < request.thresholds.null_spike_delta:
                continue
            payload: dict[str, object] = {
                "column": column,
                "baseline_null_rate": baseline_rate,
                "current_null_rate": current_rate,
                "delta": delta,
                "threshold": request.thresholds.null_spike_delta,
            }
            results.append(
                _result(
                    request=request,
                    incident_type="null_spike",
                    severity=IncidentSeverity.MEDIUM,
                    summary=f"{column} null rate가 baseline 대비 급증했다.",
                    payload=payload,
                    discriminator=column,
                )
            )
        return results

    def _detect_schema_drift(
        self,
        request: DetectionRequest,
    ) -> list[DetectionResult]:
        if request.baseline.schema_hash == request.current.schema_hash:
            return []
        payload: dict[str, object] = {
            "baseline_schema_hash": request.baseline.schema_hash,
            "current_schema_hash": request.current.schema_hash,
        }
        return [
            _result(
                request=request,
                incident_type="schema_drift",
                severity=IncidentSeverity.HIGH,
                summary="schema hash가 baseline과 다르다.",
                payload=payload,
            )
        ]

    def _detect_freshness_delay(
        self,
        request: DetectionRequest,
    ) -> list[DetectionResult]:
        delay = request.baseline.freshness_at - request.current.freshness_at
        threshold = timedelta(minutes=request.thresholds.freshness_delay_minutes)
        if delay < threshold:
            return []
        delay_minutes = delay.total_seconds() / 60
        payload: dict[str, object] = {
            "baseline_freshness_at": request.baseline.freshness_at.isoformat(),
            "current_freshness_at": request.current.freshness_at.isoformat(),
            "delay_minutes": delay_minutes,
            "threshold_minutes": request.thresholds.freshness_delay_minutes,
        }
        return [
            _result(
                request=request,
                incident_type="freshness_delay",
                severity=IncidentSeverity.HIGH,
                summary="freshness가 baseline 대비 지연되었다.",
                payload=payload,
            )
        ]


def detect_basic_incidents(request: DetectionRequest) -> list[DetectionResult]:
    """기본 detector를 실행한다."""

    return BasicIncidentDetector().detect(request)


def _result(
    *,
    request: DetectionRequest,
    incident_type: str,
    severity: IncidentSeverity,
    summary: str,
    payload: dict[str, object],
    discriminator: str | None = None,
) -> DetectionResult:
    evidence = _evidence(
        current=request.current,
        incident_type=incident_type,
        summary=summary,
        payload=payload,
        discriminator=discriminator,
    )
    incident = _incident(
        current=request.current,
        owner=request.owner,
        incident_type=incident_type,
        severity=severity,
        evidence_id=evidence.evidence_id,
        discriminator=discriminator,
    )
    return DetectionResult(incident=incident, evidence=evidence)


def _evidence(
    *,
    current: ProfileSnapshot,
    incident_type: str,
    summary: str,
    payload: dict[str, object],
    discriminator: str | None,
) -> Evidence:
    return Evidence(
        evidence_id=_contract_id(
            prefix="ev",
            incident_type=incident_type,
            current=current,
            discriminator=discriminator,
        ),
        source=EvidenceSource.PROFILE,
        asset_name=current.asset_name,
        partition=current.partition,
        observed_at=current.observed_at,
        summary=summary,
        payload={
            "rule": incident_type,
            "snapshot_id": current.snapshot_id,
            **payload,
        },
    )


def _incident(
    *,
    current: ProfileSnapshot,
    owner: str,
    incident_type: str,
    severity: IncidentSeverity,
    evidence_id: str,
    discriminator: str | None,
) -> Incident:
    return Incident(
        incident_id=_contract_id(
            prefix="inc",
            incident_type=incident_type,
            current=current,
            discriminator=discriminator,
        ),
        asset_name=current.asset_name,
        partition=current.partition,
        incident_type=incident_type,
        severity=severity,
        status=IncidentStatus.DETECTED,
        owner=owner,
        evidence_refs=[evidence_id],
        recommended_actions=_recommended_actions(incident_type),
    )


def _contract_id(
    *,
    prefix: str,
    incident_type: str,
    current: ProfileSnapshot,
    discriminator: str | None,
) -> str:
    parts = [
        prefix,
        incident_type,
        _normalize_token(current.asset_name),
        current.partition.replace("-", "_"),
    ]
    if discriminator is not None:
        parts.append(_normalize_token(discriminator))
    return "_".join(parts)


def _normalize_token(value: str) -> str:
    return "".join(
        character if character.isalnum() else "_"
        for character in value.lower()
    ).strip("_")


def _recommended_actions(incident_type: str) -> list[str]:
    return {
        "volume_drop": ["validate_source_partition", "check_ingestion_run"],
        "null_spike": ["inspect_source_columns", "add_dbt_not_null_test"],
        "schema_drift": ["compare_schema_contract", "validate_dbt_build"],
        "freshness_delay": ["check_upstream_freshness", "prepare_backfill_review"],
    }[incident_type]
