# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "duckdb>=1.3.0",
#     "marimo>=0.23.9",
# ]
# ///

import marimo

__generated_with = "0.23.9"
app = marimo.App()


@app.cell
def _(mo):
    mo.md(r"""
    # HMDA 2025 컬럼 목록 확인
    """)
    return


@app.cell
def _():
    import notebooks._notebook_init  # noqa: F401
    import marimo as mo

    return (mo,)


@app.cell
def _():
    data_path = "data/raw/hmda/year_2025.csv"
    return (data_path,)


@app.cell
def _(data_path, mo):
    mo.md(
        f"""
        ## 원천 파일

        - 경로: `{data_path}`
        - 형식: CSV
        - 목적: 컬럼명과 추론 타입 확인
        """
    )
    return


@app.cell
def _(data_path, mo):
    _df = mo.sql(
        f"""
        SELECT
            column_name,
            column_type
        FROM (
            DESCRIBE SELECT *
            FROM read_csv_auto(
                '{data_path}',
                header=true,
                nullstr=['NA', ''],
                sample_size=200000,
                ignore_errors=true
            )
        )
        ORDER BY column_name
        """
    )
    return


if __name__ == "__main__":
    app.run()
