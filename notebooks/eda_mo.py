import marimo

__generated_with = "0.23.15"
app = marimo.App(width="medium", sql_output="polars")


@app.cell
def _():
    import marimo as mo  # isort: skip

    return (mo,)


@app.cell
def _():
    import json
    import os
    from pathlib import Path

    import altair as alt
    import polars as pl

    from project_pivot.hmda_data import analyze_hmda_csv

    os.chdir(Path(__file__).resolve().parent.parent)
    return Path, alt, analyze_hmda_csv, json, os, pl


@app.cell
def _(mo):
    run_eda = mo.ui.checkbox(value=True, label="EDA 계산 실행")
    data_is_sample_ui = mo.ui.checkbox(value=True, label="샘플 데이터 사용")
    return data_is_sample_ui, run_eda


@app.cell
def _(Path, data_is_sample_ui, mo, os):
    data_is_sample = data_is_sample_ui.value
    if data_is_sample:
        data_path = os.environ.get(
            "HMDA_EDA_DATA_PATH", "data/sample/hmda/year_2025.csv"
        )
    else:
        data_path = os.environ.get("HMDA_EDA_DATA_PATH", "data/raw/hmda/year_2025.csv")

    csv_options = {
        "header": True,
        "nullstr": ["NA", ""],
        "sample_size": 200_000,
    }

    duckdb_config = {
        "memory_limit": "2GB",
        "threads": 2,
        "temp_directory": str(Path(os.environ.get("TMPDIR", "/tmp")).resolve()),
    }

    mo.md(
        f"""
        ## 입력 범위

        - data_path: `{data_path}`
        - CSV type inference sample: `{csv_options["sample_size"]:,}` rows
        - null 처리: `NA`, 빈 문자열
        - parse 오류: fail-fast
        - DuckDB 제한:
          - memory: `{duckdb_config["memory_limit"]}`
          - threads: `{duckdb_config["threads"]}`
          - spill: `{duckdb_config["temp_directory"]}`
        """
    )
    return csv_options, data_path, duckdb_config


@app.cell
def _(analyze_hmda_csv, data_path, duckdb_config, mo, run_eda):
    mo.stop(
        not run_eda.value,
        mo.callout("전체 파일 baseline 실행이 해제되어 있습니다.", kind="neutral"),
    )

    eda_evidence = analyze_hmda_csv(
        data_path,
        memory_limit=duckdb_config["memory_limit"],
        threads=duckdb_config["threads"],
        temp_directory=duckdb_config["temp_directory"],
    )
    return (eda_evidence,)


@app.cell
def _(eda_evidence):
    required_schema = eda_evidence["schema"]["required_columns"]
    return (required_schema,)


@app.cell
def _(eda_evidence):
    row_count = eda_evidence["row_count"]
    activity_year_counts = eda_evidence["activity_year_counts"]
    null_baseline = [
        {
            "column": column,
            "null_count": null_count,
            "null_rate": eda_evidence["null_rates"][column],
        }
        for column, null_count in eda_evidence["null_counts"].items()
    ]
    return activity_year_counts, null_baseline, row_count


@app.cell
def _(eda_evidence, json):
    json.dumps(eda_evidence, ensure_ascii=True)
    return


@app.cell
def _(mo, required_schema):
    schema_issues = [row for row in required_schema if row["status"] != "valid"]
    schema_status = (
        mo.callout("Required schema: valid", kind="success")
        if not schema_issues
        else mo.callout(
            "Required schema mismatch: "
            + ", ".join(f"{row['column']} ({row['status']})" for row in schema_issues),
            kind="warn",
        )
    )
    mo.vstack(
        [
            mo.md("## Required source schema"),
            schema_status,
            mo.ui.table(required_schema),
        ]
    )
    return


@app.cell
def _(activity_year_counts, alt, mo, pl, row_count):
    if activity_year_counts:
        year_df = pl.DataFrame(activity_year_counts)
        volume_chart = (
            alt.Chart(year_df)
            .mark_bar(color="#3182bd")
            .encode(
                x=alt.X("activity_year:O", title="Activity Year"),
                y=alt.Y("row_count:Q", title="Row Count"),
                tooltip=["activity_year", "row_count"],
            )
            .properties(
                title="Activity Year별 파티션 행 수 분포", width=500, height=250
            )
        )
        partition_volume = mo.vstack([mo.ui.table(activity_year_counts), volume_chart])
    else:
        partition_volume = mo.callout(
            "activity_year가 없어 partition volume은 미측정입니다.", kind="warn"
        )

    mo.vstack(
        [
            mo.md(
                f"## Volume baseline\n\n전체 row count: **{row_count:,}**\n\n"
                "`baseline`과 `current`는 비교 입력 역할 label입니다. "
                "이 노트북은 production lifecycle을 실행하지 않습니다."
            ),
            partition_volume,
        ]
    )
    return


@app.cell
def _(alt, mo, null_baseline, pl):
    null_df = pl.DataFrame(null_baseline)
    null_chart = (
        alt.Chart(null_df)
        .mark_bar(color="#e6550d")
        .encode(
            x=alt.X("null_rate:Q", title="Null Rate", axis=alt.Axis(format="%")),
            y=alt.Y("column:N", title="Column", sort="-x"),
            tooltip=["column", "null_count", alt.Tooltip("null_rate:Q", format=".2%")],
        )
        .properties(title="필수 컬럼별 Null 비율 Baseline", width=500, height=200)
    )

    mo.vstack(
        [
            mo.md("## Required column null baseline"),
            mo.md("입력에서 `NA`와 빈 문자열을 null로 해석합니다."),
            mo.ui.table(null_baseline),
            null_chart,
        ]
    )
    return


@app.cell
def _(eda_evidence, json, mo):
    evidence_json = json.dumps(eda_evidence, ensure_ascii=False, indent=2)
    mo.vstack(
        [
            mo.md(
                "## Core evidence\n\n"
                "화면 렌더링은 JSON-serializable `eda_evidence`와 분리됩니다."
            ),
            mo.accordion(
                {"EDA evidence JSON": mo.md(f"```json\n{evidence_json}\n```")}
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
