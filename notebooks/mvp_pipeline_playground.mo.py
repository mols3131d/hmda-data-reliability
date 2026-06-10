# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.23.9",
# ]
# ///

import marimo

__generated_with = "0.23.6"
app = marimo.App()


@app.cell
def _(mo):
    mo.md(r"""
    # MVP Pipeline Playground

    로컬 DuckDB에 적재된 NYC Taxi 데이터로 MVP 파이프라인을 직접 확인하는 노트북입니다.

    ```text
    raw -> dbt -> metadata/profile evidence -> detection
      -> impact -> remediation -> approval/backfill -> evaluation
    ```
    """)
    return


@app.cell
def _():
    from datetime import UTC, date, datetime
    from pathlib import Path

    import duckdb
    import marimo as mo
    from _notebook_init import notebook_init

    notebook_init()

    from project_pivot.reliability import (
        Approval,
        ApprovalStatus,
        ApprovedBackfillRequest,
        DetectionRequest,
        EvaluationCaseResult,
        ImpactAnalysisRequest,
        ProfileSnapshotRequest,
        RemediationDraftRequest,
        TableMetadataEvidenceRequest,
        analyze_dbt_impact,
        build_evaluation_report,
        create_profile_snapshot,
        create_remediation_draft,
        create_table_metadata_evidence,
        detect_basic_incidents,
        execute_approved_backfill,
        write_evaluation_report,
    )
    from project_pivot.taxi_data import DuckDBConnectionManager

    return (
        Approval,
        ApprovalStatus,
        ApprovedBackfillRequest,
        DetectionRequest,
        DuckDBConnectionManager,
        EvaluationCaseResult,
        ImpactAnalysisRequest,
        Path,
        ProfileSnapshotRequest,
        RemediationDraftRequest,
        TableMetadataEvidenceRequest,
        UTC,
        analyze_dbt_impact,
        build_evaluation_report,
        create_profile_snapshot,
        create_remediation_draft,
        create_table_metadata_evidence,
        date,
        datetime,
        detect_basic_incidents,
        duckdb,
        execute_approved_backfill,
        mo,
        write_evaluation_report,
    )


@app.cell
def _(Path, UTC, date, datetime):
    database_path = Path("data/project_pivot.duckdb")
    source_root = Path("data/raw/tlc")
    partition_day = date(2024, 1, 15)
    observed_at = datetime(2026, 6, 10, 0, 0, tzinfo=UTC)

    asset_name = "source.project_pivot.raw.yellow_tripdata"
    raw_table_name = "raw.yellow_tripdata"
    partition_column = "tpep_pickup_datetime"
    profile_columns = ("total_amount", "passenger_count")
    freshness_column = "tpep_dropoff_datetime"
    source_parquet = source_root / "yellow_tripdata_2024-01.parquet"
    return (
        asset_name,
        database_path,
        freshness_column,
        observed_at,
        partition_column,
        partition_day,
        profile_columns,
        raw_table_name,
        source_parquet,
        source_root,
    )


@app.cell
def _(database_path, mo, source_root):
    source_files = sorted(source_root.glob("yellow_tripdata_2024-*.parquet"))
    zone_csv_path = source_root / "taxi_zone_lookup.csv"

    mo.md(
        f"""
        ## 1. 입력 파일과 DB

        - DuckDB: `{database_path}` / exists={database_path.exists()}
        - Taxi zone CSV: `{zone_csv_path}` / exists={zone_csv_path.exists()}
        - Yellow tripdata files: `{len(source_files)}`

        raw table이 없으면 터미널에서 먼저 실행하세요.

        ```bash
        env UV_CACHE_DIR=/tmp/uv-cache PYTHONPATH=src \\
          uv run python -m project_pivot.taxi_data.cli load-raw \\
          --database data/project_pivot.duckdb \\
          --source-root data/raw/tlc \\
          --year 2024
        ```
        """
    )
    return


@app.cell
def _(database_path, duckdb, mo):
    raw_summary = None
    raw_summary_error = None
    if database_path.exists():
        connection = duckdb.connect(str(database_path), read_only=True)
        try:
            raw_summary = {
                "taxi_zones": connection.execute(
                    "SELECT count(*) FROM raw.taxi_zones"
                ).fetchone()[0],
                "yellow_tripdata": connection.execute(
                    "SELECT count(*) FROM raw.yellow_tripdata"
                ).fetchone()[0],
                "pickup_date_minmax": connection.execute(
                    """
                    SELECT
                        min(CAST(tpep_pickup_datetime AS DATE)),
                        max(CAST(tpep_pickup_datetime AS DATE))
                    FROM raw.yellow_tripdata
                    """
                ).fetchone(),
            }
        except Exception as exc:
            raw_summary_error = f"{type(exc).__name__}: {exc}"
        finally:
            connection.close()

    mo.md(
        f"""
        ## 2. raw table 상태

        ```python
        {raw_summary if raw_summary_error is None else raw_summary_error}
        ```
        """
    )
    return


@app.cell
def _(Path, mo):
    manifest_path = Path("dbt/target/manifest.json")
    run_results_path = Path("dbt/target/run_results.json")
    dbt_artifacts_ready = manifest_path.exists() and run_results_path.exists()

    mo.md(
        f"""
        ## 3. dbt artifact

        - manifest: `{manifest_path}` / exists={manifest_path.exists()}
        - run results: `{run_results_path}` / exists={run_results_path.exists()}

        artifact가 없으면 터미널에서 실행하세요.

        ```bash
        env UV_CACHE_DIR=/tmp/uv-cache uv run dbt build \\
          --project-dir dbt --profiles-dir dbt
        ```
        """
    )
    return manifest_path, run_results_path


@app.cell
def _(database_path, duckdb, mo):
    mart_preview = []
    mart_preview_error = None
    if database_path.exists():
        connection = duckdb.connect(str(database_path), read_only=True)
        try:
            mart_preview = [
                {
                    "pickup_date": str(row[0]),
                    "pickup_location_id": int(row[1]),
                    "trip_count": int(row[2]),
                    "total_amount": float(row[3]),
                    "total_passenger_count": int(row[4]),
                }
                for row in connection.execute(
                    """
                    SELECT
                        pickup_date,
                        pickup_location_id,
                        trip_count,
                        total_amount,
                        total_passenger_count
                    FROM marts.mart_daily_taxi_trips
                    ORDER BY pickup_date, pickup_location_id
                    LIMIT 10
                    """
                ).fetchall()
            ]
        except Exception as exc:
            mart_preview_error = f"{type(exc).__name__}: {exc}"
        finally:
            connection.close()

    mo.md("## 4. mart preview")
    if mart_preview_error is None:
        mo.ui.table(mart_preview)
    else:
        mo.md(f"`{mart_preview_error}`")
    return


@app.cell
def _(
    DetectionRequest,
    DuckDBConnectionManager,
    ProfileSnapshotRequest,
    TableMetadataEvidenceRequest,
    asset_name,
    create_profile_snapshot,
    create_table_metadata_evidence,
    database_path,
    detect_basic_incidents,
    freshness_column,
    observed_at,
    partition_column,
    partition_day,
    profile_columns,
    raw_table_name,
):
    metadata_evidence = None
    baseline_snapshot = None
    current_snapshot = None
    detection_results = []
    primary_detection = None
    pipeline_error = None

    try:
        with DuckDBConnectionManager(database_path, read_only=True) as connection:
            metadata_evidence = create_table_metadata_evidence(
                connection,
                TableMetadataEvidenceRequest(
                    asset_name=asset_name,
                    table_name=raw_table_name,
                    observed_at=observed_at,
                ),
            )
            profile_request = ProfileSnapshotRequest(
                asset_name=asset_name,
                table_name=raw_table_name,
                partition_column=partition_column,
                partition=partition_day,
                profile_columns=profile_columns,
                freshness_column=freshness_column,
                observed_at=observed_at,
            )
            baseline_snapshot = create_profile_snapshot(connection, profile_request)
    except Exception as exc:
        pipeline_error = f"{type(exc).__name__}: {exc}"

    if baseline_snapshot is not None:
        reduced_row_count = max(1, baseline_snapshot.row_count // 4)
        current_snapshot = baseline_snapshot.model_copy(
            update={
                "snapshot_id": "profile_playground_current",
                "row_count": reduced_row_count,
                "metric_values": {"row_count": float(reduced_row_count)},
            }
        )
        detection_results = detect_basic_incidents(
            DetectionRequest(
                baseline=baseline_snapshot,
                current=current_snapshot,
            )
        )
        primary_detection = detection_results[0] if detection_results else None
    return (
        baseline_snapshot,
        detection_results,
        metadata_evidence,
        pipeline_error,
        primary_detection,
        profile_request,
    )


@app.cell
def _(
    baseline_snapshot,
    detection_results,
    metadata_evidence,
    mo,
    pipeline_error,
):
    if pipeline_error is not None:
        mo.md(f"## 5. evidence/profile/detection\n\n`{pipeline_error}`")
    else:
        detected_incident_types = [
            result.incident.incident_type for result in detection_results
        ]
        mo.md(
            f"""
            ## 5. evidence/profile/detection

            - metadata source: `{metadata_evidence.source}`
            - metadata row_count: `{metadata_evidence.payload["row_count"]}`
            - partition row_count: `{baseline_snapshot.row_count}`
            - detected incidents: `{detected_incident_types}`
            """
        )
    return


@app.cell
def _(
    ImpactAnalysisRequest,
    RemediationDraftRequest,
    analyze_dbt_impact,
    create_remediation_draft,
    manifest_path,
    primary_detection,
    run_results_path,
):
    impact_result = None
    remediation_draft = None
    lifecycle_error = None

    if (
        primary_detection is not None
        and manifest_path.exists()
        and run_results_path.exists()
    ):
        try:
            impact_result = analyze_dbt_impact(
                ImpactAnalysisRequest(
                    incident=primary_detection.incident,
                    dbt_manifest_path=manifest_path,
                    dbt_run_results_path=run_results_path,
                )
            )
            remediation_draft = create_remediation_draft(
                RemediationDraftRequest(
                    incident=impact_result.incident,
                    evidence=primary_detection.evidence,
                    lineage_evidence=impact_result.lineage_evidence,
                )
            )
        except Exception as exc:
            lifecycle_error = f"{type(exc).__name__}: {exc}"
    return impact_result, lifecycle_error, remediation_draft


@app.cell
def _(impact_result, lifecycle_error, mo, remediation_draft):
    if lifecycle_error is not None:
        mo.md(f"## 6. impact/remediation\n\n`{lifecycle_error}`")
    elif impact_result is None or remediation_draft is None:
        mo.md("## 6. impact/remediation\n\ndbt artifact 또는 detection 결과가 없습니다.")
    else:
        mo.md(
            f"""
            ## 6. impact/remediation

            - affected asset count: `{len(impact_result.incident.affected_assets)}`
            - first affected assets: `{impact_result.incident.affected_assets[:5]}`
            - recommended actions: `{remediation_draft.recommended_actions}`
            - backfill actions: `{remediation_draft.backfill_actions}`
            - validation actions: `{remediation_draft.validation_actions}`
            """
        )
    return


@app.cell
def _(mo):
    run_backfill = mo.ui.switch(label="승인 backfill 실행", value=False)
    mo.vstack([run_backfill])
    return (run_backfill,)


@app.cell
def _(
    Approval,
    ApprovalStatus,
    ApprovedBackfillRequest,
    DuckDBConnectionManager,
    database_path,
    execute_approved_backfill,
    observed_at,
    partition_day,
    primary_detection,
    profile_request,
    remediation_draft,
    run_backfill,
    source_parquet,
):
    backfill_result = None
    backfill_error = None

    if (
        run_backfill.value
        and primary_detection is not None
        and remediation_draft is not None
    ):
        try:
            approval = Approval(
                approval_id=f"approval_playground_{partition_day.isoformat()}",
                incident_id=primary_detection.incident.incident_id,
                status=ApprovalStatus.APPROVED,
                requested_by="data-platform",
                requested_at=observed_at,
                approved_by="data-owner",
                approved_at=observed_at,
                requested_actions=remediation_draft.backfill_actions,
            )
            with DuckDBConnectionManager(database_path) as connection:
                backfill_result = execute_approved_backfill(
                    connection,
                    ApprovedBackfillRequest(
                        approval=approval,
                        parquet_paths=(source_parquet,),
                        partition_date=partition_day,
                        profile_request=profile_request,
                    ),
                )
        except Exception as exc:
            backfill_error = f"{type(exc).__name__}: {exc}"
    return backfill_error, backfill_result


@app.cell
def _(backfill_error, backfill_result, mo, run_backfill):
    if not run_backfill.value:
        mo.md(
            "## 7. approved backfill\n\n"
            "스위치를 켜면 승인된 partition overwrite를 실행합니다."
        )
    elif backfill_error is not None:
        mo.md(f"## 7. approved backfill\n\n`{backfill_error}`")
    else:
        mo.md(
            f"""
            ## 7. approved backfill

            - row_count: `{backfill_result.row_count}`
            - validation_passed: `{backfill_result.validation_passed}`
            - executed_actions: `{backfill_result.executed_actions}`
            """
        )
    return


@app.cell
def _(
    EvaluationCaseResult,
    Path,
    build_evaluation_report,
    impact_result,
    observed_at,
    primary_detection,
    remediation_draft,
    write_evaluation_report,
):
    evaluation_report = None
    evaluation_report_path = None

    if primary_detection is not None and remediation_draft is not None:
        evidence_refs = [primary_detection.evidence.evidence_id]
        if impact_result is not None:
            evidence_refs.append(impact_result.lineage_evidence.lineage_id)

        evaluation_report = build_evaluation_report(
            [
                EvaluationCaseResult(
                    case_name="notebook_volume_drop",
                    expected_incident_types=["volume_drop"],
                    detected_incident_types=[primary_detection.incident.incident_type],
                    required_actions=["prepare_partition_backfill"],
                    remediation_actions=remediation_draft.recommended_actions,
                    evidence_refs=evidence_refs,
                )
            ],
            generated_at=observed_at,
        )
        evaluation_report_path = write_evaluation_report(
            evaluation_report,
            Path("scratch/evaluation/notebook_pipeline_report.md"),
        )
    return evaluation_report, evaluation_report_path


@app.cell
def _(evaluation_report, evaluation_report_path, mo):
    if evaluation_report is None:
        mo.md("## 8. evaluation report\n\n생성할 detection 결과가 없습니다.")
    else:
        mo.md(
            f"""
            ## 8. evaluation report

            - output: `{evaluation_report_path}`
            - detection_success_rate: `{evaluation_report.detection_success_rate:.2%}`
            - action_success_rate: `{evaluation_report.action_success_rate:.2%}`
            """
        )
    return


if __name__ == "__main__":
    app.run()
