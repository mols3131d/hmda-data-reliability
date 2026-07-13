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
    # `_common.py` 마이크로 월드

    production의 필수 컬럼 검증 함수를 직접 호출해 집합 계약을 관찰한다.

    ```text
    필수 컬럼 집합 - 실제 컬럼 집합 = 누락 컬럼
    ```

    실제 구현: `src/project_pivot/hmda_data/ingestion/_common.py`
    """)
    return


@app.cell
def _():
    import duckdb
    import marimo as mo
    import polars as pl

    from project_pivot.data_platform.sql import quote_identifier
    from project_pivot.hmda_data.errors import HMDADataValidationError
    from project_pivot.hmda_data.ingestion._common import (
        REQUIRED_HMDA_COLUMNS,
        validate_required_columns,
    )
    from sandboxes._notebook_init import notebook_init

    notebook_init()
    return (
        HMDADataValidationError,
        REQUIRED_HMDA_COLUMNS,
        duckdb,
        mo,
        pl,
        quote_identifier,
        validate_required_columns,
    )


@app.cell
def _(mo):
    column_scenario = mo.ui.dropdown(
        options={
            "필수 컬럼 모두 존재": "valid",
            "income 누락": "missing_income",
            "income·county_code 누락": "missing_multiple",
            "필수 컬럼 + extra_note": "extra_column",
        },
        value="필수 컬럼 모두 존재",
        label="테이블 컬럼 시나리오",
        full_width=True,
    )
    mo.vstack(
        [
            mo.md("## 1. 컬럼 계약 선택"),
            mo.md("실행 전에 검증 성공 여부와 `missing_columns` 값을 예상하세요."),
            column_scenario,
        ]
    )
    return (column_scenario,)


@app.cell
def _(REQUIRED_HMDA_COLUMNS, column_scenario):
    excluded_columns_by_scenario = {
        "valid": set(),
        "missing_income": {"income"},
        "missing_multiple": {"income", "county_code"},
        "extra_column": set(),
    }
    expected_columns = set(REQUIRED_HMDA_COLUMNS)
    actual_column_names = sorted(
        expected_columns - excluded_columns_by_scenario[column_scenario.value]
    )
    if column_scenario.value == "extra_column":
        actual_column_names.append("extra_note")
    return actual_column_names, expected_columns


@app.cell
def _(
    HMDADataValidationError,
    actual_column_names,
    duckdb,
    expected_columns,
    pl,
    quote_identifier,
    validate_required_columns,
):
    table_name = "hmda_contract"
    column_definitions = ", ".join(
        f"{quote_identifier(column_name)} VARCHAR"
        for column_name in actual_column_names
    )

    with duckdb.connect() as _connection:
        _connection.execute(
            f"CREATE TABLE {quote_identifier(table_name)} ({column_definitions})"
        )
        described_columns = {
            str(row[0])
            for row in _connection.execute(
                f"DESCRIBE {quote_identifier(table_name)}"
            ).fetchall()
        }
        try:
            validate_required_columns(_connection, table_name)
            validation_passed = True
            validation_message = "필수 컬럼 검증에 성공했습니다."
            validation_context = {}
        except HMDADataValidationError as error:
            validation_passed = False
            validation_message = str(error)
            validation_context = error.context

    missing_columns = sorted(expected_columns - described_columns)
    contract_rows = []
    for column_name in sorted(expected_columns | described_columns):
        if column_name in missing_columns:
            status = "누락"
        elif column_name not in expected_columns:
            status = "추가"
        else:
            status = "충족"
        contract_rows.append(
            {
                "column_name": column_name,
                "필수": column_name in expected_columns,
                "실제": column_name in described_columns,
                "상태": status,
            }
        )
    contract_frame = pl.DataFrame(contract_rows)
    return (
        contract_frame,
        missing_columns,
        validation_context,
        validation_message,
        validation_passed,
    )


@app.cell
def _(
    contract_frame,
    missing_columns,
    mo,
    validation_context,
    validation_message,
    validation_passed,
):
    validation_output = mo.callout(
        f"**{validation_message}**\n\n"
        f"missing_columns: `{missing_columns}`\n\n"
        f"context: `{validation_context}`",
        kind="success" if validation_passed else "danger",
    )
    mo.vstack(
        [
            mo.md("## 2. production 검증 결과"),
            validation_output,
            mo.ui.table(contract_frame, selection=None, page_size=10),
        ]
    )
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## 관찰 포인트

    - 값의 유효성이나 Null 여부가 아니라 **컬럼 존재 여부**만 검증한다.
    - 추가 컬럼은 허용한다.
    - 누락 컬럼은 정렬되어 예외 `context`에 기록된다.
    - `actual_column_count`는 누락 수가 아니라 실제 테이블의 전체 컬럼 수다.

    ## 이해 확인

    - `income` 값이 전부 Null이어도 이 검증은 통과하는가?
    - `extra_note`가 있어도 통과하는 이유는 무엇인가?
    - 두 컬럼을 누락했을 때 예외 context에는 어떤 값들이 들어가는가?
    """)
    return


if __name__ == "__main__":
    app.run()
