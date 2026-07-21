"""Incident lifecycle 단계 경계 테스트."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from project_pivot.data_operations import (
    DataOperationError,
    DataOperationRequest,
    run_incident_lifecycle,
    runner,
)
from project_pivot.data_platform.duckdb import DuckDBConnectionManager
from project_pivot.reliability import (
    ProfileSnapshot,
    ProfileSnapshotRequest,
    create_profile_snapshot,
)

pytestmark = pytest.mark.component


def test_lifecycle_compares_baseline_with_actual_current(tmp_path: Path) -> None:
    """합성값 대신 DuckDB partition의 실제 current를 비교한다."""

    request = _prepare_request(tmp_path)
    baseline = _baseline_snapshot(
        request,
        row_count=8,
        null_rates={"income": 0.0, "loan_amount": 0.0},
    )

    result = run_incident_lifecycle(request, baseline)

    assert result.metadata_row_count == 4
    assert result.baseline_row_count == 8
    assert result.current_row_count == 4
    assert result.detected_incident_types == ["volume_drop", "null_spike"]


def test_lifecycle_analyzes_all_detections_in_order(tmp_path: Path) -> None:
    """모든 incident의 영향과 조치를 순서 보존·중복 제거해 반환한다."""

    request = _prepare_request(tmp_path)
    baseline = _baseline_snapshot(
        request,
        row_count=10,
        null_rates={"income": 0.0, "loan_amount": 0.0},
    )

    result = run_incident_lifecycle(request, baseline)

    assert result.detected_incident_types == ["volume_drop", "null_spike"]
    assert result.evidence_refs == [
        "ev_volume_drop_source_project_pivot_raw_hmda_loans_2025",
        "lineage_source_project_pivot_raw_hmda_loans_2025",
        "ev_null_spike_source_project_pivot_raw_hmda_loans_2025_loan_amount",
    ]
    assert result.affected_assets == [
        "stg_hmda_loans",
        "mart_hmda_loan_outcomes",
    ]
    assert result.recommended_actions == [
        "validate_source_partition",
        "check_ingestion_run",
        "prepare_partition_backfill",
        "inspect_source_columns",
        "add_dbt_not_null_test",
    ]
    assert result.backfill_actions == ["prepare_partition_backfill"]
    assert result.validation_actions == [
        "rerun_profile_snapshot",
        "rerun_dbt_build",
        "validate_null_rate",
    ]


def test_lifecycle_skips_impact_when_no_incident(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """정상 profile은 빈 요약을 반환하고 impact analysis를 호출하지 않는다."""

    request = _prepare_request(tmp_path)
    baseline = _current_snapshot(request)

    def fail_on_impact(*args: object, **kwargs: object) -> None:
        pytest.fail("incident가 없을 때 impact analysis를 실행하면 안 됩니다.")

    monkeypatch.setattr(
        "project_pivot.data_operations.incident_lifecycle.analyze_dbt_impact",
        fail_on_impact,
    )

    result = run_incident_lifecycle(request, baseline)

    assert result.detected_incident_types == []
    assert result.evidence_refs == []
    assert result.affected_assets == []
    assert result.recommended_actions == []
    assert result.backfill_actions == []
    assert result.validation_actions == []


def test_runner_reexports_incident_lifecycle() -> None:
    """기존 runner module import 경로를 유지한다."""

    assert runner.run_incident_lifecycle is run_incident_lifecycle


@pytest.mark.parametrize(
    ("baseline_update", "expected_context"),
    [
        ({"asset_name": "raw.other"}, "asset"),
        ({"partition": "2024"}, "partition"),
    ],
)
def test_lifecycle_rejects_incompatible_baseline(
    tmp_path: Path,
    baseline_update: dict[str, object],
    expected_context: str,
) -> None:
    """비교할 수 없는 baseline을 데이터 작업 오류로 거부한다."""

    request = _prepare_request(tmp_path)
    baseline = _current_snapshot(request).model_copy(update=baseline_update)

    with pytest.raises(DataOperationError, match=expected_context):
        run_incident_lifecycle(request, baseline)


def test_lifecycle_has_no_recovery_or_evaluation_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """탐지 후에도 target partition과 파일 시스템을 변경하지 않는다."""

    monkeypatch.chdir(tmp_path)
    request = _prepare_request(tmp_path)
    baseline = _baseline_snapshot(request, row_count=10)

    result = run_incident_lifecycle(request, baseline)

    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        row_count = connection.execute(
            "SELECT count(*) FROM raw.hmda_loans WHERE activity_year = 2025"
        ).fetchone()
    assert row_count == (4,)
    assert not (tmp_path / "scratch").exists()
    assert "evaluation_report_path" not in type(result).model_fields
    assert "backfill_validation_passed" not in type(result).model_fields


def _prepare_request(tmp_path: Path) -> DataOperationRequest:
    database_path = tmp_path / "project_pivot.duckdb"
    with DuckDBConnectionManager(database_path) as connection:
        connection.execute("CREATE SCHEMA raw")
        connection.execute(
            """
            CREATE TABLE raw.hmda_loans (
                activity_year INTEGER,
                loan_amount DOUBLE,
                income DOUBLE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO raw.hmda_loans VALUES
                (2025, 350000, 120),
                (2025, NULL, 130),
                (2025, 420000, 95),
                (2025, NULL, 95)
            """
        )

    target = tmp_path / "dbt" / "target"
    target.mkdir(parents=True)
    manifest = {
        "sources": {
            "source.project_pivot.raw.hmda_loans": {
                "name": "hmda_loans",
                "schema": "raw",
                "resource_type": "source",
                "depends_on": {"nodes": []},
            }
        },
        "nodes": {
            "model.project_pivot.stg_hmda_loans": {
                "name": "stg_hmda_loans",
                "resource_type": "model",
                "depends_on": {"nodes": ["source.project_pivot.raw.hmda_loans"]},
            },
            "model.project_pivot.mart_hmda_loan_outcomes": {
                "name": "mart_hmda_loan_outcomes",
                "resource_type": "model",
                "depends_on": {"nodes": ["model.project_pivot.stg_hmda_loans"]},
            },
        },
    }
    manifest_path = target / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    run_results_path = target / "run_results.json"
    run_results_path.write_text("{}", encoding="utf-8")
    return DataOperationRequest(
        database_path=database_path,
        dbt_manifest_path=manifest_path,
        dbt_run_results_path=run_results_path,
        observed_at=datetime(2026, 7, 19, 0, 0, tzinfo=UTC),
    )


def _current_snapshot(request: DataOperationRequest) -> ProfileSnapshot:
    assert request.observed_at is not None
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        return create_profile_snapshot(
            connection,
            ProfileSnapshotRequest(
                asset_name=request.asset_name,
                table_name=request.raw_table_name,
                partition_column=request.partition_column,
                partition=request.source_year,
                profile_columns=request.profile_columns,
                freshness_column=request.freshness_column,
                observed_at=request.observed_at,
            ),
        )


def _baseline_snapshot(
    request: DataOperationRequest,
    *,
    row_count: int,
    null_rates: dict[str, float] | None = None,
) -> ProfileSnapshot:
    current = _current_snapshot(request)
    baseline_null_rates = null_rates or current.null_rates
    metric_values = {
        **current.metric_values,
        "row_count": float(row_count),
        **{
            f"{column}.null_count": row_count * null_rate
            for column, null_rate in baseline_null_rates.items()
        },
    }
    return current.model_copy(
        update={
            "row_count": row_count,
            "null_rates": baseline_null_rates,
            "metric_values": metric_values,
        }
    )
