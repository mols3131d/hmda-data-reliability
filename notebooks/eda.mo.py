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
    # NYC Taxi Data Quality EDA
    이 노트북은 `data/raw/tlc` 원천 데이터의 통계와 품질 이상치
    (아웃라이어, Null 등) 상태를 분석하기 위한 간단한 EDA 도구입니다.
    """)
    return


@app.cell
def _():
    from _notebook_init import notebook_init
    import duckdb
    import marimo as mo
    import polars as pl

    notebook_init()
    return (mo,)


@app.cell
def _():
    data_path = "data/raw/tlc/yellow_tripdata_2024-01.parquet"
    return (data_path,)


@app.cell
def _(data_path, mo):
    _df = mo.sql(
        f"""
        CREATE
        OR REPLACE TABLE my_table AS
        SELECT
            *
        FROM
            read_parquet ('{data_path}')
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT
            *
        FROM
            my_table
        LIMIT
            5
        """
    )
    return


@app.cell
def _(data_path, mo):
    _df = mo.sql(
        f"""
        DESCRIBE '{data_path}'
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        PRAGMA table_info (my_table)
        """
    )
    return


@app.cell
def _(mo):
    _df = mo.sql(
        f"""
        SELECT 
            column_name,
            data_type
        FROM
            information_schema.columns
        WHERE
            table_name = 'my_table'
        """
    )
    return


if __name__ == "__main__":
    app.run()
