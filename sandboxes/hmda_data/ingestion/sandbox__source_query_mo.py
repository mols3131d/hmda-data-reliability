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
    from pathlib import Path

    from project_pivot.hmda_data.ingestion._source_query import (
        validate_source_paths,
    )
    from sandboxes._notebook_init import notebook_init

    notebook_init()
    return Path, validate_source_paths


@app.cell
def _(Path, validate_source_paths):
    data_path = Path("data/year_2025_sample.csv")
    validate_source_paths(source_paths=[data_path])
    return


if __name__ == "__main__":
    app.run()
