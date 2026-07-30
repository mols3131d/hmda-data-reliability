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
    from pathlib import Path

    import duckdb
    import marimo as mo

    os.chdir(Path(__file__).resolve().parent.parent)
    return duckdb, hashlib, json, mo, os


@app.cell
def _(os):
    data_path = os.environ.get("HMDA_EDA_DATA_PATH", "data/year_2025_sample.csv")
    csv_options = {
        "header": True,
        "nullstr": ["NA", ""],
        "sample_size": 200_000,
        "ignore_errors": True,
    }
    return csv_options, data_path


@app.cell
def _(csv_options, data_path, mo):
    mo.md(f"""
        ## 입력 범위

        - 경로: `{data_path}`
        - 분석 범위: 파일 전체
        - CSV type inference sample: `{csv_options["sample_size"]:,}` rows
        - null 처리: `NA`, 빈 문자열
        - soft-fail parse: `ignore_errors={str(csv_options["ignore_errors"]).lower()}`

        `ignore_errors=true`이므로 파싱 불가 행이 있어도 분석은 계속됩니다.
        이 출력은 원천 탐색 evidence이며 저장된 `ProfileSnapshot`이 아닙니다.
        """)
    return


@app.cell
def _(data_path, duckdb):
    connection = duckdb.connect()
    source_relation = connection.sql(
        """
        SELECT * FROM read_csv_auto(
            $data_path, header=true, nullstr=['NA', ''],
            sample_size=200000, ignore_errors=true
        )
        """,
        params={"data_path": data_path},
    )
    source_relation.create_view("hmda_eda_source", replace=True)
    return connection, source_relation


@app.cell
def _(hashlib, json, source_relation):
    schema_rows = [
        {"name": name, "type": str(column_type)}
        for name, column_type in zip(
            source_relation.columns, source_relation.types, strict=True
        )
    ]
    inferred_types = {row["name"]: row["type"] for row in schema_rows}
    schema_payload = json.dumps(
        sorted(schema_rows, key=lambda row: row["name"]),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    schema_hash = f"sha256:{hashlib.sha256(schema_payload.encode()).hexdigest()}"
    return inferred_types, schema_hash, schema_rows


@app.cell
def _(connection, inferred_types):
    def quote_identifier(identifier):
        return f'"{identifier.replace(chr(34), chr(34) * 2)}"'

    profile_columns = list(inferred_types)
    metric_select = ["count(*) AS row_count"] + [
        f"count(*) FILTER (WHERE {quote_identifier(column)} IS NULL) "
        f"AS {quote_identifier(column)}"
        for column in profile_columns
    ]
    metric_values = connection.execute(
        f"SELECT {', '.join(metric_select)} FROM hmda_eda_source"
    ).fetchall()[0]
    row_count = metric_values[0]
    null_baseline = [
        {
            "column": column,
            "null_count": null_count,
            "null_rate": null_count / row_count if row_count else 0.0,
        }
        for column, null_count in zip(profile_columns, metric_values[1:], strict=True)
    ]
    null_rates = {row["column"]: row["null_rate"] for row in null_baseline}
    activity_year_counts = (
        [
            {"activity_year": year, "row_count": count}
            for year, count in connection.execute(
                "SELECT activity_year, count(*) FROM hmda_eda_source "
                "GROUP BY activity_year ORDER BY activity_year"
            ).fetchall()
        ]
        if "activity_year" in inferred_types
        else []
    )
    return activity_year_counts, null_baseline, null_rates, row_count


@app.cell
def _(connection, inferred_types):
    freshness_value = (
        connection.execute(
            'SELECT max(try_cast("observed_at" AS TIMESTAMP)) FROM hmda_eda_source'
        ).fetchall()[0][0]
        if "observed_at" in inferred_types
        else None
    )
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
    data_path,
    freshness,
    json,
    null_baseline,
    null_rates,
    row_count,
    schema_hash,
    schema_rows,
):
    eda_evidence = {
        "source": {"path": data_path, "scope": "full_file", "csv_options": csv_options},
        "row_count": row_count,
        "activity_year_counts": activity_year_counts,
        "null_counts": {row["column"]: row["null_count"] for row in null_baseline},
        "null_rates": null_rates,
        "schema": {"columns": schema_rows, "schema_hash": schema_hash},
        "freshness": freshness,
    }
    json.dumps(eda_evidence, ensure_ascii=True)
    return (eda_evidence,)


@app.cell
def _(mo, schema_rows):
    mo.vstack(
        [
            mo.md("## Source schema"),
            mo.ui.table(schema_rows),
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
            mo.md("## Null baseline\n\n입력에서 `NA`와 빈 문자열을 null로 해석합니다."),
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
