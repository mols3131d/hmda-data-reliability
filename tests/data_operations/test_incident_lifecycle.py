"""Incident lifecycle 단계 경계 테스트."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from hmda_reliability.data_operations import (
    DataOperationError,
    DataOperationRequest,
    run_incident_lifecycle,
    runner,
)
from hmda_reliability.data_platform.duckdb import DuckDBConnectionManager
from hmda_reliability.reliability import (
    DetectionThresholds,
    ProfileSnapshot,
    ProfileSnapshotRequest,
    create_profile_snapshot,
)


@pytest.mark.integration
def test_lifecycle_compares_baseline_with_actual_current(tmp_path: Path) -> None:
    """합성값 대신 DuckDB partition의 실제 current를 비교한다."""

    request = _prepare_request(tmp_path)
    baseline = _baseline_snapshot(
        request,
        row_count=8,
        null_rates={"income": 0.0, "loan_amount": 0.0},
    )
    with DuckDBConnectionManager(request.database_path) as connection:
        connection.execute(
            """
            INSERT INTO raw.hmda_loans VALUES
                (2024, 999999, 999, 2024, 'other.csv', TIMESTAMPTZ '2026-07-19')
            """
        )

    result = run_incident_lifecycle(request, baseline)

    assert result.metadata_row_count == 5
    assert result.baseline_row_count == 8
    assert result.current_row_count == 4
    assert result.detected_incident_types == ["volume_drop", "null_spike"]
    assert result.target_content_identity is not None
    assert result.target_content_identity.table_name == "raw.hmda_loans"
    assert result.target_content_identity.source_year == 2025
    assert result.target_content_identity.row_count == 4
    assert result.dbt_projection_id is not None


@pytest.mark.integration
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
    assert result.detected_incident_ids == [
        "inc_volume_drop_source_hmda_reliability_raw_hmda_loans_2025",
        "inc_null_spike_source_hmda_reliability_raw_hmda_loans_2025_loan_amount",
    ]
    assert result.evidence_refs == [
        "ev_volume_drop_source_hmda_reliability_raw_hmda_loans_2025",
        "lineage_source_hmda_reliability_raw_hmda_loans_2025",
        "ev_null_spike_source_hmda_reliability_raw_hmda_loans_2025_loan_amount",
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


@pytest.mark.integration
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
        "hmda_reliability.data_operations.incident_lifecycle.analyze_dbt_impact",
        fail_on_impact,
    )

    result = run_incident_lifecycle(request, baseline)

    assert result.detected_incident_ids == []
    assert result.detected_incident_types == []
    assert result.evidence_refs == []
    assert result.affected_assets == []
    assert result.recommended_actions == []
    assert result.backfill_actions == []
    assert result.validation_actions == []
    assert result.target_content_identity is None
    assert result.dbt_projection_id is None


@pytest.mark.unit
def test_runner_reexports_incident_lifecycle() -> None:
    """기존 runner module import 경로를 유지한다."""

    assert runner.run_incident_lifecycle is run_incident_lifecycle


@pytest.mark.integration
def test_lifecycle_forwards_explicit_freshness_threshold(tmp_path: Path) -> None:
    request = _prepare_request(tmp_path).model_copy(
        update={
            "freshness_column": "ingested_at",
            "observed_at": datetime(2026, 7, 19, 2, 0, tzinfo=UTC),
        }
    )
    baseline = _current_snapshot(request)

    explicit = run_incident_lifecycle(
        request,
        baseline,
        thresholds=DetectionThresholds(freshness_max_age_minutes=1_440),
    )
    default = run_incident_lifecycle(request, baseline)

    assert "freshness_delay" not in explicit.detected_incident_types
    assert "freshness_delay" in default.detected_incident_types


@pytest.mark.integration
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


@pytest.mark.integration
def test_lifecycle_has_no_recovery_or_evaluation_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """같은 row count의 값 변경과 approval·report 파일 생성도 허용하지 않는다."""

    monkeypatch.chdir(tmp_path)
    request = _prepare_request(tmp_path)
    baseline = _baseline_snapshot(request, row_count=10)
    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        rows_before = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY ALL"
        ).fetchall()
    artifact_bytes_before = {
        path: path.read_bytes()
        for path in (request.dbt_manifest_path, request.dbt_run_results_path)
    }
    files_before = {path for path in tmp_path.rglob("*") if path.is_file()}

    result = run_incident_lifecycle(request, baseline)

    with DuckDBConnectionManager(request.database_path, read_only=True) as connection:
        rows_after = connection.execute(
            "SELECT * FROM raw.hmda_loans ORDER BY ALL"
        ).fetchall()
    assert result.detected_incident_types == ["volume_drop"]
    assert rows_after == rows_before
    assert {path: path.read_bytes() for path in artifact_bytes_before} == (
        artifact_bytes_before
    )
    # Current projection을 읽는 shared lock file 생성은 read-only 계약에 허용된다.
    projection_lock = request.dbt_manifest_path.parent / ".artifact-promotion.lock"
    files_after = {path for path in tmp_path.rglob("*") if path.is_file()}
    assert files_after - {projection_lock} == files_before
    assert not (tmp_path / "scratch").exists()
    assert "evaluation_report_path" not in type(result).model_fields
    assert "backfill_validation_passed" not in type(result).model_fields


@pytest.mark.integration
def test_lifecycle_evaluates_new_year_partition_synthetic_defect(
    tmp_path: Path,
) -> None:
    """2026년 신규 파티션의 합성 결함 산출물을 인제스션하여 격리 환경에서
    사고 탐지, 계통 영향, 구체적 권고 조치를 검증하고 메인 DB 무변경을 보장한다.
    """

    from hmda_reliability.hmda_data import load_hmda_loans_partition, null_spike

    main_db = tmp_path / "hmda_reliability.duckdb"
    request_base = _prepare_request(tmp_path)

    # 1. 2025년 원천 CSV 픽스처 생성
    source_dir = tmp_path / "raw"
    source_dir.mkdir(parents=True)
    source_file = source_dir / "year_2025.csv"
    source_file.write_text(
        "\n".join(
            [
                "activity_year,loan_amount,income,loan_purpose,action_taken,"
                "state_code,county_code,loan_type",
                "2025,350000,120,1,1,CA,06001,conventional",
                "2025,400000,150,1,1,CA,06001,conventional",
                "2025,500000,180,1,1,CA,06001,conventional",
                "2025,600000,200,1,1,CA,06001,conventional",
            ]
        ),
        encoding="utf-8",
    )

    # 2. 실제 null_spike() 생성기로 2026년 합성 결함 Parquet 생성
    cases_dir = tmp_path / "cases"
    with DuckDBConnectionManager() as conn:
        defect_path = null_spike(
            conn,
            [source_file],
            cases_dir,
            target_column="income",
            null_fraction=0.5,
            target_year=2026,
            case_name="null_spike_2026",
        )

    # 3. 샌드박스 DB에 파티션 인제스션 함수로 적재 (E2E 파이프라인 결합)
    sandbox_db = tmp_path / "sandbox_2026.duckdb"
    with DuckDBConnectionManager(sandbox_db) as conn:
        loaded_rows = load_hmda_loans_partition(
            conn,
            [defect_path],
            2026,
            source_file="null_spike_2026.parquet",
            table_name="raw.hmda_loans",
        )
    assert loaded_rows == 4

    request = request_base.model_copy(
        update={
            "database_path": sandbox_db,
            "source_year": 2026,
            "source_file": "null_spike_2026.parquet",
            "observed_at": datetime(2026, 9, 3, 0, 0, tzinfo=UTC),
        }
    )

    baseline = _baseline_snapshot(
        request,
        row_count=4,
        null_rates={"income": 0.0, "loan_amount": 0.0},
    )

    # 4. 신뢰성 수명주기 실행 및 엄격한 단언 검증
    result = run_incident_lifecycle(request, baseline)

    assert result.current_row_count == 4
    assert result.detected_incident_types == ["null_spike"]
    assert "stg_hmda_loans" in result.affected_assets
    assert "mart_hmda_loan_outcomes" in result.affected_assets
    assert result.recommended_actions == [
        "inspect_source_columns",
        "add_dbt_not_null_test",
        "validate_source_partition",
    ]
    assert any("null_spike" in ref and "2026" in ref for ref in result.evidence_refs)

    # 5. 메인 데이터베이스(main_db)의 상태 무변경 단언 검증
    with DuckDBConnectionManager(main_db, read_only=True) as conn:
        main_rows = conn.execute(
            "SELECT count(*) FROM raw.hmda_loans WHERE activity_year = 2025"
        ).fetchone()
        main_2026 = conn.execute(
            "SELECT count(*) FROM raw.hmda_loans WHERE activity_year = 2026"
        ).fetchone()
    assert main_rows == (4,)
    assert main_2026 == (0,)


def _prepare_request(tmp_path: Path) -> DataOperationRequest:
    database_path = tmp_path / "hmda_reliability.duckdb"
    with DuckDBConnectionManager(database_path) as connection:
        connection.execute("CREATE SCHEMA raw")
        connection.execute(
            """
            CREATE TABLE raw.hmda_loans (
                activity_year INTEGER,
                loan_amount DOUBLE,
                income DOUBLE,
                source_year INTEGER,
                source_file_name VARCHAR,
                ingested_at TIMESTAMPTZ
            )
            """
        )
        connection.execute(
            """
            INSERT INTO raw.hmda_loans VALUES
                (2025, 350000, 120, 2025, 'fixture.csv', TIMESTAMPTZ '2026-07-19'),
                (2025, NULL, 130, 2025, 'fixture.csv', TIMESTAMPTZ '2026-07-19'),
                (2025, 420000, 95, 2025, 'fixture.csv', TIMESTAMPTZ '2026-07-19'),
                (2025, NULL, 95, 2025, 'fixture.csv', TIMESTAMPTZ '2026-07-19')
            """
        )

    target = tmp_path / "dbt" / "target"
    target.mkdir(parents=True)
    manifest = {
        "sources": {
            "source.hmda_reliability.raw.hmda_loans": {
                "name": "hmda_loans",
                "schema": "raw",
                "resource_type": "source",
                "depends_on": {"nodes": []},
            }
        },
        "nodes": {
            "model.hmda_reliability.stg_hmda_loans": {
                "name": "stg_hmda_loans",
                "resource_type": "model",
                "depends_on": {"nodes": ["source.hmda_reliability.raw.hmda_loans"]},
            },
            "model.hmda_reliability.mart_hmda_loan_outcomes": {
                "name": "mart_hmda_loan_outcomes",
                "resource_type": "model",
                "depends_on": {"nodes": ["model.hmda_reliability.stg_hmda_loans"]},
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
