# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "duckdb>=1.3.0",
#     "marimo>=0.23.9",
#     "polars>=1.41.2",
#     "pydantic>=2.11.0",
# ]
# ///

import marimo

__generated_with = "0.23.9"
app = marimo.App()


@app.cell
def _(mo):
    mo.md(r"""
    # HMDA ingest 샌드박스

    실제 원천 파일에서 작은 샘플을 만들고 `raw.hmda_loans` 적재 결과를 직접
    확인한다. 모든 출력은 `tmp/hmda_ingestion_sandbox/`에 저장하며 운영 DB는
    변경하지 않는다.

    진행 순서: **입력 확인 → 직접 ingest → DuckDB 조회 → 멱등성 확인 → Dagster 비교**
    """)
    return


@app.cell
def _():
    from itertools import islice
    from pathlib import Path

    import duckdb
    import marimo as mo
    import polars as pl

    from project_pivot.pipeline import PipelineRunRequest, load_raw_data
    from sandboxes._notebook_init import notebook_init

    notebook_init()
    return Path, PipelineRunRequest, duckdb, islice, load_raw_data, mo, pl


@app.cell
def _(Path):
    source_path = Path("data/raw/hmda/year_2025.csv")
    sandbox_root = Path("tmp/hmda_ingestion_sandbox")
    sample_root = sandbox_root / "input"
    sample_path = sample_root / "year_2025.csv"
    direct_database_path = sandbox_root / "direct.duckdb"
    dagster_database_path = sandbox_root / "dagster.duckdb"
    dagster_config_path = sandbox_root / "dagster_run.yaml"
    return (
        dagster_config_path,
        dagster_database_path,
        direct_database_path,
        sample_path,
        sample_root,
        sandbox_root,
        source_path,
    )


@app.cell
def _(mo):
    sample_row_count = mo.ui.number(
        start=1,
        stop=100,
        step=1,
        value=5,
        label="샘플 행 수",
    )
    mo.vstack(
        [
            mo.md("## 1. 입력 범위 선택"),
            sample_row_count,
            mo.md(
                "행 수를 바꾸면 샘플 파일과 샌드박스 DB가 같은 "
                "파티션으로 다시 적재됩니다."
            ),
        ]
    )
    return (sample_row_count,)


@app.cell
def _(islice, mo, sample_path, sample_root, sample_row_count, source_path):
    mo.stop(
        not source_path.is_file(),
        mo.callout(f"원천 파일을 찾을 수 없습니다: `{source_path}`", kind="danger"),
    )

    selected_row_count = int(sample_row_count.value or 5)
    with source_path.open(encoding="utf-8", newline="") as source_file:
        sample_lines = list(islice(source_file, selected_row_count + 1))

    mo.stop(
        len(sample_lines) <= 1,
        mo.callout("원천 파일에 데이터 행이 없습니다.", kind="danger"),
    )

    sample_root.mkdir(parents=True, exist_ok=True)
    sample_path.write_text("".join(sample_lines), encoding="utf-8")
    actual_sample_row_count = len(sample_lines) - 1
    return (actual_sample_row_count,)


@app.cell
def _(actual_sample_row_count, duckdb, mo, sample_path):
    with duckdb.connect() as _connection:
        sample_preview = _connection.execute(
            """
            SELECT
                activity_year,
                state_code,
                county_code,
                loan_purpose,
                action_taken,
                loan_amount,
                income
            FROM read_csv_auto(
                ?,
                header = true,
                nullstr = ['NA', '']
            )
            LIMIT ?
            """,
            [sample_path.as_posix(), actual_sample_row_count],
        ).pl()

    mo.vstack(
        [
            mo.callout(
                f"`{sample_path}`에 데이터 "
                f"{actual_sample_row_count:,}행을 만들었습니다.",
                kind="success",
            ),
            mo.ui.table(sample_preview, selection=None, page_size=10),
        ]
    )
    return


@app.cell
def _(PipelineRunRequest, direct_database_path, load_raw_data, sample_root):
    ingest_request = PipelineRunRequest(
        database_path=direct_database_path,
        source_root=sample_root,
        source_year=2025,
        run_dbt_build=False,
    )
    first_load_result = load_raw_data(ingest_request)
    return first_load_result, ingest_request


@app.cell
def _(direct_database_path, duckdb, pl):
    with duckdb.connect(direct_database_path.as_posix(), read_only=True) as _connection:
        schema_rows = _connection.execute("DESCRIBE raw.hmda_loans").fetchall()
        schema_frame = pl.DataFrame(
            schema_rows,
            schema=[
                "column_name",
                "column_type",
                "null",
                "key",
                "default",
                "extra",
            ],
            orient="row",
        )
        partition_frame = _connection.sql(
            """
            SELECT
                source_year,
                source_file_name,
                count(*) AS row_count,
                count(*) FILTER (WHERE ingested_at IS NULL)
                    AS missing_ingested_at,
                min(ingested_at) AS ingested_at
            FROM raw.hmda_loans
            GROUP BY source_year, source_file_name
            ORDER BY source_year, source_file_name
            """
        ).pl()
        ingested_rows_frame = _connection.sql(
            """
            SELECT
                activity_year,
                state_code,
                county_code,
                loan_purpose,
                action_taken,
                loan_amount,
                income,
                source_file_name,
                source_year,
                ingested_at
            FROM raw.hmda_loans
            ORDER BY activity_year, state_code, county_code
            LIMIT 20
            """
        ).pl()
        first_ingested_at = _connection.execute(
            "SELECT min(ingested_at) FROM raw.hmda_loans"
        ).fetchone()[0]
    return (
        first_ingested_at,
        ingested_rows_frame,
        partition_frame,
        schema_frame,
    )


@app.cell
def _(
    first_load_result,
    ingested_rows_frame,
    mo,
    partition_frame,
    schema_frame,
):
    mo.vstack(
        [
            mo.md("## 2. 직접 ingest 결과"),
            mo.callout(
                f"`load_raw_data()`가 {first_load_result.hmda_loans_row_count:,}행을 "
                "적재했습니다.",
                kind="success",
            ),
            mo.md("### 파티션과 추적 컬럼"),
            mo.ui.table(partition_frame, selection=None, page_size=10),
            mo.md("### 적재된 행"),
            mo.ui.table(ingested_rows_frame, selection=None, page_size=10),
            mo.accordion(
                {
                    "전체 스키마 보기": mo.ui.table(
                        schema_frame,
                        selection=None,
                        page_size=20,
                    )
                }
            ),
        ]
    )
    return


@app.cell
def _(mo):
    rerun_ingest = mo.ui.run_button(
        label="같은 파티션 다시 적재",
        kind="warn",
    )
    mo.vstack(
        [
            mo.md("## 3. 멱등성 확인"),
            mo.md(
                "버튼을 누르면 같은 입력을 다시 적재합니다. 총행 수는 같고 "
                "`ingested_at`만 바뀌어야 합니다."
            ),
            rerun_ingest,
        ]
    )
    return (rerun_ingest,)


@app.cell
def _(
    direct_database_path,
    duckdb,
    first_ingested_at,
    first_load_result,
    ingest_request,
    load_raw_data,
    mo,
    pl,
    rerun_ingest,
):
    mo.stop(not rerun_ingest.value)

    second_load_result = load_raw_data(ingest_request)
    with duckdb.connect(direct_database_path.as_posix(), read_only=True) as _connection:
        second_ingested_at = _connection.execute(
            "SELECT min(ingested_at) FROM raw.hmda_loans"
        ).fetchone()[0]

    idempotency_frame = pl.DataFrame(
        {
            "실행": ["1차", "2차"],
            "행 수": [
                first_load_result.hmda_loans_row_count,
                second_load_result.hmda_loans_row_count,
            ],
            "ingested_at": [first_ingested_at, second_ingested_at],
        }
    )
    idempotent = (
        first_load_result.hmda_loans_row_count
        == second_load_result.hmda_loans_row_count
    )
    return idempotency_frame, idempotent


@app.cell
def _(idempotency_frame, idempotent, mo):
    mo.vstack(
        [
            mo.callout(
                "행 수가 유지됐습니다. 파티션 교체가 멱등하게 동작합니다."
                if idempotent
                else "행 수가 달라졌습니다. 적재 경로를 다시 확인하세요.",
                kind="success" if idempotent else "danger",
            ),
            mo.ui.table(idempotency_frame, selection=None),
        ]
    )
    return


@app.cell
def _(
    dagster_config_path,
    dagster_database_path,
    direct_database_path,
    sample_root,
    sandbox_root,
):
    dagster_config_path.write_text(
        "\n".join(
            [
                "resources:",
                "  pipeline:",
                "    config:",
                f"      database_path: {dagster_database_path.as_posix()}",
                f"      source_root: {sample_root.as_posix()}",
                "      source_year: 2025",
                "      run_dbt_build: false",
                "",
            ]
        ),
        encoding="utf-8",
    )
    dagster_command = (
        "PYTHONPATH=src uv run dg launch "
        "--assets raw_hmda_loans "
        f"--config {dagster_config_path.as_posix()}"
    )
    sandbox_paths = {
        "샘플 입력": sample_root,
        "직접 실행 DB": direct_database_path,
        "Dagster 실행 DB": dagster_database_path,
        "Dagster 설정": dagster_config_path,
        "샌드박스 루트": sandbox_root,
    }
    return dagster_command, sandbox_paths


@app.cell
def _(dagster_command, mo, sandbox_paths):
    path_lines = "\n".join(
        f"- {label}: `{path}`" for label, path in sandbox_paths.items()
    )
    mo.md(
        f"""
        ## 4. Dagster 실행과 비교

        노트북은 ingest 로직을 직접 호출했습니다. 같은 샘플을 Dagster asset으로
        실행하려면 프로젝트 루트의 터미널에서 다음 명령을 실행하세요.

        ```bash
        {dagster_command}
        ```

        Dagster는 같은 `load_raw_data()`를 호출하고 실행 이력과 materialization
        metadata를 추가합니다.

        ### 샌드박스 경로

        {path_lines}
        """
    )
    return


@app.cell
def _(mo):
    refresh_dagster_result = mo.ui.run_button(
        label="Dagster 결과 확인",
        kind="success",
    )
    mo.vstack([refresh_dagster_result])
    return (refresh_dagster_result,)


@app.cell
def _(
    dagster_database_path,
    direct_database_path,
    duckdb,
    mo,
    pl,
    refresh_dagster_result,
):
    mo.stop(not refresh_dagster_result.value)
    mo.stop(
        not dagster_database_path.is_file(),
        mo.callout(
            "Dagster DB가 없습니다. 위의 `dg launch` 명령을 먼저 실행하세요.",
            kind="warn",
        ),
    )

    comparison_rows = []
    for execution_name, database_path in (
        ("직접 실행", direct_database_path),
        ("Dagster", dagster_database_path),
    ):
        with duckdb.connect(database_path.as_posix(), read_only=True) as _connection:
            row = _connection.execute(
                """
                SELECT
                    count(*) AS row_count,
                    count(DISTINCT source_file_name) AS source_file_count,
                    min(source_year) AS source_year
                FROM raw.hmda_loans
                """
            ).fetchone()
        comparison_rows.append(
            {
                "실행 경로": execution_name,
                "행 수": row[0],
                "파일 수": row[1],
                "source_year": row[2],
            }
        )

    dagster_comparison_frame = pl.DataFrame(comparison_rows)
    return (dagster_comparison_frame,)


@app.cell
def _(dagster_comparison_frame, mo):
    mo.vstack(
        [
            mo.callout(
                "두 DB의 데이터 계약이 같은지 비교하세요. 실행 이력의 차이는 "
                "Dagster UI에서 확인합니다.",
                kind="info",
            ),
            mo.ui.table(dagster_comparison_frame, selection=None),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 완료 질문

    - `source_year`은 원천 행이 아니라 어디에서 만들어졌는가?
    - staging 검증은 `DELETE` 전인가, 후인가?
    - 같은 파티션을 다시 적재했을 때 행 수가 유지되는 이유는 무엇인가?
    - 직접 실행과 Dagster 실행에서 데이터가 같아야 하는 이유는 무엇인가?

    네 질문에 답할 수 있으면 ingest 경계를 이해한 것이다. dbt나 incident
    lifecycle은 이 샌드박스의 범위에 포함하지 않는다.
    """)
    return


if __name__ == "__main__":
    app.run()
