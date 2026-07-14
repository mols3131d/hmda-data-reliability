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
def _():
    from project_pivot.data_platform.duckdb import (
        DuckDBConnectionManager,
        table_columns,
        table_row_count,
    )
    from sandboxes._notebook_init import notebook_init

    notebook_init()
    return DuckDBConnectionManager, table_columns, table_row_count


@app.cell
def _(DuckDBConnectionManager):
    manager = DuckDBConnectionManager(database_path="data/project_pivot.duckdb")

    with manager as _connection:
        _connection.sql(query="SHOW DATABASES").show()
        _connection.sql(query="SHOW SCHEMAS").show()
        _connection.sql(query="SHOW ALL TABLES").show()
        _connection.sql(query="DESCRIBE raw.hmda_loans").show()
        _connection.sql(query="SELECT count(*) FROM raw.hmda_loans").show()
        _connection.sql(query="SELECT * FROM raw.hmda_loans LIMIT 10").show()
    return (manager,)


@app.cell
def _(manager, table_row_count):
    with manager as _connection:
        row_count = table_row_count(
            connection=_connection,
            table_name="raw.hmda_loans",
        )

    print(row_count)
    return


@app.cell
def _(manager, table_columns):
    with manager as _connection:
        columns = table_columns(
            connection=_connection,
            table_name="raw.hmda_loans",
        )

    print(f"컬럼 수: {len(columns)}")
    print(*sorted(columns), sep=", ")
    return


if __name__ == "__main__":
    app.run()
