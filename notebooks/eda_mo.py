# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "duckdb>=1.3.0",
#     "marimo>=0.23.9",
# ]
# ///

import marimo

__generated_with = "0.23.14"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md(r"""
    # HMDA 원천 EDA baseline
    """)
    return


@app.cell
def _():
    import json
    import os
    from pathlib import Path

    import marimo as mo

    from project_pivot.hmda_data import analyze_hmda_csv

    os.chdir(Path(__file__).resolve().parent.parent)
    return Path, analyze_hmda_csv, json, mo, os


@app.cell
def _(Path, os):
    data_path = os.environ.get("HMDA_EDA_DATA_PATH", "data/raw/hmda/year_2025.csv")
    input_path = Path(data_path).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"HMDA EDA input file does not exist: {input_path}")

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
    return csv_options, data_path, duckdb_config, input_path


@app.cell
def _(csv_options, data_path, duckdb_config, input_path, mo):
    run_eda = mo.ui.run_button(label="전체 파일 baseline 실행", kind="warn")
    mo.vstack(
        [
            mo.md(
                f"""
                ## 입력 범위

                - 요청 경로: `{data_path}`
                - resolved 경로: `{input_path}`
                - 분석 범위: 파일 전체
                - CSV type inference sample: `{csv_options["sample_size"]:,}` rows
                - null 처리: `NA`, 빈 문자열
                - parse 오류: fail-fast
                - DuckDB 제한:
                  - memory: `{duckdb_config["memory_limit"]}`
                  - threads: `{duckdb_config["threads"]}`
                  - spill: `{duckdb_config["temp_directory"]}`

                버튼을 눌러야 전체 파일 scan을 시작합니다.
                파일 부재 또는 DuckDB CSV parse 오류 시 baseline metric과
                `eda_evidence`를 생성하지 않습니다.
                """
            ),
            run_eda,
        ]
    )
    return (run_eda,)


@app.cell
def _(analyze_hmda_csv, duckdb_config, input_path, mo, run_eda):
    mo.stop(
        not run_eda.value,
        mo.callout("전체 파일 baseline은 아직 실행하지 않았습니다.", kind="neutral"),
    )

    eda_evidence = analyze_hmda_csv(
        input_path,
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
def _(eda_evidence):
    freshness = eda_evidence["freshness"]
    return (freshness,)


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
def _(activity_year_counts, mo, row_count):
    partition_volume = (
        mo.ui.table(activity_year_counts)
        if activity_year_counts
        else mo.callout(
            "activity_year가 없어 partition volume은 미측정입니다.", kind="warn"
        )
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
def _(mo, null_baseline):
    mo.vstack(
        [
            mo.md("## Required column null baseline"),
            mo.md("입력에서 `NA`와 빈 문자열을 null로 해석합니다."),
            mo.ui.table(null_baseline),
        ]
    )
    return


@app.cell
def _(freshness, mo):
    freshness_status = (
        mo.callout(f"Source freshness: {freshness['freshness_at']}", kind="success")
        if freshness["status"] == "measured"
        else mo.callout(
            "Source freshness: 미측정. 유효한 observed_at이 없습니다. "
            "파일 수정 시각은 filesystem metadata이며 data freshness가 아닙니다. "
            "Bronze ingested_at은 별도 raw-table 경로의 ingestion time입니다.",
            kind="warn",
        )
    )
    mo.vstack([mo.md("## Freshness boundary"), freshness_status])
    return


@app.cell
def _(eda_evidence, json, mo):
    profile_mapping = [
        {
            "eda_evidence": "row_count",
            "ProfileSnapshot": "row_count",
            "role": "baseline/current value",
        },
        {
            "eda_evidence": "null_rates",
            "ProfileSnapshot": "null_rates",
            "role": "baseline/current value",
        },
        {
            "eda_evidence": "schema.schema_hash",
            "ProfileSnapshot": "schema_hash",
            "role": "display-only mapping",
        },
        {
            "eda_evidence": "freshness.freshness_at",
            "ProfileSnapshot": "freshness_at",
            "role": "None when unmeasured",
        },
    ]
    evidence_json = json.dumps(eda_evidence, ensure_ascii=False, indent=2)
    mo.vstack(
        [
            mo.md(
                "## Profile evidence mapping\n\n"
                "화면 렌더링은 JSON-serializable `eda_evidence`와 분리됩니다."
            ),
            mo.ui.table(profile_mapping),
            mo.accordion(
                {"EDA evidence JSON": mo.md(f"```json\n{evidence_json}\n```")}
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
