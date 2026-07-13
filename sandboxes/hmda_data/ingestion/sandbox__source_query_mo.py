# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "duckdb>=1.3.0",
#     "marimo>=0.23.9",
#     "polars>=1.41.2",
# ]
# ///

import marimo

__generated_with = "0.23.9"
app = marimo.App()


@app.cell
def _(mo):
    mo.md(r"""
    # `_source_query.py` 마이크로 월드

    production의 경로 정규화와 SQL 생성 함수를 직접 호출해 다음 변환을 관찰한다.

    ```text
    파일 경로 → 형식별 reader SQL → UNION ALL BY NAME → 추적 컬럼
    ```

    실제 구현: `src/project_pivot/hmda_data/ingestion/_source_query.py`
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import duckdb
    import marimo as mo
    import polars as pl

    from project_pivot.hmda_data.errors import HMDADataLoadError
    from project_pivot.hmda_data.ingestion._source_query import (
        normalize_source_paths,
        source_union_sql,
    )
    from sandboxes._notebook_init import notebook_init

    notebook_init()
    return (
        HMDADataLoadError,
        Path,
        duckdb,
        mo,
        normalize_source_paths,
        pl,
        source_union_sql,
    )


@app.cell
def _(Path):
    sandbox_root = Path("tmp/hmda_source_query_sandbox")
    input_root = sandbox_root / "input"
    csv_path = input_root / "year_2025.csv"
    parquet_path = input_root / "hmda_2024.parquet"
    unsupported_path = input_root / "hmda_2025.json"
    return csv_path, input_root, parquet_path, unsupported_path


@app.cell
def _(csv_path, input_root, parquet_path, pl, unsupported_path):
    input_root.mkdir(parents=True, exist_ok=True)
    csv_path.write_text(
        "\n".join(
            [
                "activity_year,loan_purpose,action_taken,loan_amount,income,state_code,county_code",
                "2025,1,1,350000,120,CA,06001",
                "2025,31,3,420000,95,NY,36061",
            ]
        ),
        encoding="utf-8",
    )
    pl.DataFrame(
        {
            "activity_year": [2024],
            "loan_purpose": [1],
            "action_taken": [2],
            "loan_amount": [250000],
            "income": [88],
            "state_code": ["TX"],
            "county_code": ["48113"],
        }
    ).write_parquet(parquet_path)
    unsupported_path.write_text("{}", encoding="utf-8")
    return


@app.cell
def _(mo):
    source_scenario = mo.ui.dropdown(
        options={
            "CSV만": "csv",
            "Parquet만": "parquet",
            "CSV + Parquet": "mixed",
            "지원하지 않는 JSON": "unsupported",
            "빈 입력": "empty",
        },
        value="CSV + Parquet",
        label="원천 경로 시나리오",
        full_width=True,
    )
    mo.vstack(
        [
            mo.md("## 1. 경로 정규화"),
            mo.md(
                "실행 전에 결과를 예상하세요. 어떤 확장자가 통과하고 "
                "어떤 예외가 발생할까요?"
            ),
            source_scenario,
        ]
    )
    return (source_scenario,)


@app.cell
def _(csv_path, parquet_path, source_scenario, unsupported_path):
    scenario_paths = {
        "csv": [csv_path],
        "parquet": [parquet_path],
        "mixed": [csv_path, parquet_path],
        "unsupported": [unsupported_path],
        "empty": [],
    }
    selected_source_paths = scenario_paths[source_scenario.value]
    return (selected_source_paths,)


@app.cell
def _(HMDADataLoadError, normalize_source_paths, selected_source_paths):
    try:
        normalized_paths = normalize_source_paths(selected_source_paths)
        normalization_error_message = None
        normalization_error_context = {}
    except HMDADataLoadError as error:
        normalized_paths = []
        normalization_error_message = str(error)
        normalization_error_context = error.context
    return (
        normalization_error_context,
        normalization_error_message,
        normalized_paths,
    )


@app.cell
def _(
    mo,
    normalization_error_context,
    normalization_error_message,
    normalized_paths,
    pl,
    selected_source_paths,
):
    if normalization_error_message is None:
        normalization_output = mo.vstack(
            [
                mo.callout("경로 정규화에 성공했습니다.", kind="success"),
                mo.ui.table(
                    pl.DataFrame(
                        {
                            "입력 경로": [
                                path.as_posix() for path in selected_source_paths
                            ],
                            "정규화 타입": [
                                type(path).__name__ for path in normalized_paths
                            ],
                            "확장자": [path.suffix for path in normalized_paths],
                        }
                    ),
                    selection=None,
                ),
            ]
        )
    else:
        normalization_output = mo.callout(
            f"**{normalization_error_message}**\n\n"
            f"context: `{normalization_error_context}`",
            kind="danger",
        )
    mo.vstack([normalization_output])
    return


@app.cell
def _(
    duckdb,
    mo,
    normalization_error_message,
    normalized_paths,
    source_union_sql,
):
    mo.stop(normalization_error_message is not None)

    generated_sql = source_union_sql(normalized_paths)
    with duckdb.connect() as _connection:
        query_result_frame = _connection.execute(
            generated_sql,
            [path.as_posix() for path in normalized_paths],
        ).pl()
    return generated_sql, query_result_frame


@app.cell
def _(generated_sql, mo, query_result_frame):
    tracking_columns = [
        "source_file",
        "source_file_name",
        "source_year",
        "ingested_at",
    ]
    visible_columns = [
        "activity_year",
        "state_code",
        "county_code",
        *tracking_columns,
    ]
    mo.vstack(
        [
            mo.md("## 2. 생성된 SQL과 실행 결과"),
            mo.accordion(
                {"production 함수가 만든 SQL": mo.md(f"```sql\n{generated_sql}\n```")}
            ),
            mo.md(
                "`?`는 경로 문자열을 SQL에 직접 삽입하지 않고 binding하는 자리입니다."
            ),
            mo.ui.table(
                query_result_frame.select(visible_columns),
                selection=None,
                page_size=10,
            ),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 이해 확인

    - CSV와 Parquet은 각각 어떤 DuckDB reader를 사용하는가?
    - 여러 파일의 컬럼 순서가 달라도 결합할 수 있는 이유는 무엇인가?
    - `source_year`은 행의 `activity_year`이 아니라 어디에서 추출하는가?
    - 지원하지 않는 확장자를 선택하면 어느 함수가 어떤 예외를 만드는가?
    """)
    return


if __name__ == "__main__":
    app.run()
