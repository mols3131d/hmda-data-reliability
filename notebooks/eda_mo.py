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
    import hashlib
    import json
    import os
    import time
    from pathlib import Path

    import duckdb
    import marimo as mo

    os.chdir(Path(__file__).resolve().parent.parent)
    return Path, duckdb, hashlib, json, mo, os, time


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
def _(duckdb, duckdb_config, input_path, mo, run_eda):
    mo.stop(
        not run_eda.value,
        mo.callout("전체 파일 baseline은 아직 실행하지 않았습니다.", kind="neutral"),
    )

    connection = duckdb.connect(config=duckdb_config)
    source_relation = connection.sql(
        """
        SELECT * FROM read_csv_auto(
            $input_path, header=true, nullstr=['NA', ''], sample_size=200000
        )
        """,
        params={"input_path": str(input_path)},
    )
    source_relation.create_view("hmda_eda_source", replace=True)
    return connection, source_relation


@app.cell
def _(hashlib, json, source_relation):
    required_columns = (
        "activity_year",
        "state_code",
        "county_code",
        "loan_purpose",
        "action_taken",
        "loan_amount",
        "income",
    )
    expected_type_families = {
        "activity_year": ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT"),
        "state_code": ("VARCHAR",),
        "county_code": ("VARCHAR",),
        "loan_purpose": ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT"),
        "action_taken": ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT"),
        "loan_amount": (
            "TINYINT",
            "SMALLINT",
            "INTEGER",
            "BIGINT",
            "HUGEINT",
            "DECIMAL",
            "DOUBLE",
        ),
        "income": (
            "TINYINT",
            "SMALLINT",
            "INTEGER",
            "BIGINT",
            "HUGEINT",
            "DECIMAL",
            "DOUBLE",
        ),
    }
    schema_rows = [
        {"name": name, "type": str(column_type)}
        for name, column_type in zip(
            source_relation.columns, source_relation.types, strict=True
        )
    ]
    inferred_types = {row["name"]: row["type"] for row in schema_rows}
    required_schema = [
        {
            "column": column,
            "inferred_type": inferred_types.get(column),
            "status": (
                "valid"
                if inferred_types.get(column) in expected_type_families[column]
                else "missing"
                if column not in inferred_types
                else "type mismatch"
            ),
        }
        for column in required_columns
    ]
    schema_payload = json.dumps(
        sorted(schema_rows, key=lambda row: row["name"]),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    schema_hash = f"sha256:{hashlib.sha256(schema_payload.encode()).hexdigest()}"
    return (
        inferred_types,
        required_columns,
        required_schema,
        schema_hash,
        schema_rows,
    )


@app.cell
def _(connection, inferred_types, required_columns, time):
    def quote_identifier(identifier):
        return f'"{identifier.replace(chr(34), chr(34) * 2)}"'

    profile_columns = [
        column for column in required_columns if column in inferred_types
    ]
    metric_select = ["count(*) AS row_count"] + [
        f"count(*) FILTER (WHERE {quote_identifier(column)} IS NULL) "
        f"AS {quote_identifier(column)}"
        for column in profile_columns
    ]
    if "observed_at" in inferred_types:
        metric_select.append(
            'max(try_cast("observed_at" AS TIMESTAMP)) AS freshness_value'
        )

    has_activity_year = "activity_year" in inferred_types
    grouping_select = (
        "activity_year, grouping(activity_year) AS is_total, "
        if has_activity_year
        else ""
    )
    grouping_clause = (
        "GROUP BY GROUPING SETS ((), (activity_year))" if has_activity_year else ""
    )
    started_at = time.monotonic()
    metric_rows = connection.execute(
        f"SELECT {grouping_select}{', '.join(metric_select)} "
        f"FROM hmda_eda_source {grouping_clause}"
    ).fetchall()
    duration_seconds = time.monotonic() - started_at

    total_row = next(row for row in metric_rows if not has_activity_year or row[1] == 1)
    metric_offset = 2 if has_activity_year else 0
    row_count = total_row[metric_offset]
    null_baseline = [
        {
            "column": column,
            "null_count": null_count,
            "null_rate": null_count / row_count if row_count else 0.0,
        }
        for column, null_count in zip(
            profile_columns,
            total_row[metric_offset + 1 : metric_offset + 1 + len(profile_columns)],
            strict=True,
        )
    ]
    null_rates = {row["column"]: row["null_rate"] for row in null_baseline}
    activity_year_counts = (
        [
            {"activity_year": row[0], "row_count": row[metric_offset]}
            for row in metric_rows
            if row[1] == 0
        ]
        if has_activity_year
        else []
    )
    freshness_value = total_row[-1] if "observed_at" in inferred_types else None
    return (
        activity_year_counts,
        duration_seconds,
        freshness_value,
        null_baseline,
        null_rates,
        row_count,
    )


@app.cell
def _(freshness_value, inferred_types):
    freshness = {
        "status": "measured" if freshness_value is not None else "unmeasured",
        "source_column": "observed_at" if "observed_at" in inferred_types else None,
        "freshness_at": freshness_value.isoformat()
        if freshness_value is not None
        else None,
        "boundary": {
            "file_mtime": "filesystem metadata; not source freshness",
            "bronze_ingested_at": "ingestion time from separate raw-table EDA path",
        },
    }
    return (freshness,)


@app.cell
def _(
    activity_year_counts,
    csv_options,
    duckdb_config,
    duration_seconds,
    freshness,
    input_path,
    json,
    null_baseline,
    null_rates,
    required_schema,
    row_count,
    schema_hash,
    schema_rows,
):
    eda_evidence = {
        "source": {
            "path": str(input_path),
            "scope": "full_file",
            "csv_options": csv_options,
            "duckdb_config": duckdb_config,
        },
        "duration_seconds": duration_seconds,
        "row_count": row_count,
        "activity_year_counts": activity_year_counts,
        "null_counts": {row["column"]: row["null_count"] for row in null_baseline},
        "null_rates": null_rates,
        "schema": {
            "columns": schema_rows,
            "required_columns": required_schema,
            "schema_hash": schema_hash,
        },
        "freshness": freshness,
    }
    json.dumps(eda_evidence, ensure_ascii=True)
    return (eda_evidence,)


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
